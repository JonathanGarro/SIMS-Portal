FROM --platform=linux/amd64 python:3.9-slim-buster
WORKDIR /app
RUN apt update && apt install -y gcc python3-dev
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "3", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "120", "run:app"]
