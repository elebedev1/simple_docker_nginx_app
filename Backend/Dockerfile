FROM python:3.12-slim

WORKDIR /app_back

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY app.py /app_back

COPY profile.html /app_back

CMD ["python", "app.py"]
