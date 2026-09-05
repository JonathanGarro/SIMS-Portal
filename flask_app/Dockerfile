FROM python:3.11-slim-bullseye
WORKDIR /app
# install system dependencies needed for compiling python packages
# libjpeg-dev, zlib1g-dev, libtiff-dev, libfreetype6-dev, liblcms2-dev, libwebp-dev for pillow
# build-essential for gcc/g++ needed by numpy, pandas, cffi
# libopenblas-dev for numpy/pandas linear algebra operations
# libffi-dev for cffi
RUN apt update && apt install -y \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libopenblas-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=run.py
# Always gunicorn here - flask run's dev server isn't meant for production, and
# this used to be a manual toggle (comment/uncomment before every deploy) tied to
# also hand-editing Config.DEBUG. Both are now driven by FLASK_DEBUG instead, so
# this image is production-safe by default. docker-compose.yml overrides this
# command back to flask run for local dev's live-reload.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "3", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "120", "run:app"]