FROM python:3.8
EXPOSE 5000/tcp
WORKDIR /flask_app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY run.py .