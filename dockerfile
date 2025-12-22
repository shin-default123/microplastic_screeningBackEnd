# Use specific Python 3.10 version
FROM python:3.10.13-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies - Use CPU versions for smaller size
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu torchvision==0.16.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    pillow==9.5.0 \  # CHANGED FROM 10.1.0 to 9.5.0
    opencv-python-headless==4.8.1.78 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    python-dotenv==1.0.0

# Install ultralytics (dependencies already installed)
RUN pip install --no-cache-dir ultralytics==8.0.196

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]