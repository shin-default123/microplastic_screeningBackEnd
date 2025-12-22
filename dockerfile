FROM python:3.10-slim

WORKDIR /app

# Install only essential system packages
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages (ultralytics includes everything needed)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    ultralytics \
    python-multipart \
    python-dotenv

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]