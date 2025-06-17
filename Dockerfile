FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#     libglib2.0-0 \
#     libsm6 \
#     libxext6 \
#     libxrender-dev \
#     libgomp1 \
#     libgtk-3-0 \
#     libavcodec-dev \
#     libavformat-dev \
#     libswscale-dev \
#     libgstreamer-plugins-base1.0-dev \
#     libgstreamer1.0-dev \
#     libpng-dev \
#     libjpeg-dev \
#     libopenexr-dev \
#     libtiff-dev \
#     libwebp-dev \
#     git \
#     wget \
#     && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run App
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]