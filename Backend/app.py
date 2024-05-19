import os
import psycopg2
from flask import Flask, request, jsonify,send_file, send_from_directory
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="bofabo72",
            host="host.docker.internal",
            port="5432"
        )
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
    return connection


@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data['username']
    email = data['email']
    password = data['password']

    if 'profilePic' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['profilePic']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        conn = create_connection()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, email, password, profile_image_path) VALUES (%s, %s, %s, %s)", 
                        (username, email, password, file_path))
            conn.commit()
            return jsonify({"message": "Registration successful!"}), 201
        except psycopg2.IntegrityError as e:
            conn.rollback()
            return jsonify({"error": "Username or email already exists", "details": str(e)}), 400
        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({"error": "Database error", "details": str(e)}), 500
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data['email']
    password = data['password']

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            username = user[1]
            profile_pic = user[4]
            
            with open('profile.html', 'r') as file:
                profile_html = file.read()
            
            
            profile_html = profile_html.replace('{{ username }}', username)
            profile_html = profile_html.replace('{{ profile_pic }}', os.path.basename(profile_pic))
            
            # Save the modified HTML to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
                temp_file.write(profile_html.encode('utf-8'))
                temp_file_path = temp_file.name

            
            return send_file(temp_file_path, mimetype='text/html')

        else:
            return jsonify({"error": "Invalid email or password"}), 401
        
    except psycopg2.Error as e:
        print(f"Error querying database: {e}")
        return jsonify({"error": "Database query error"}), 500
    finally:
        cursor.close()
        conn.close()    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
