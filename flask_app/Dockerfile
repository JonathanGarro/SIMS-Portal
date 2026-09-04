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
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]