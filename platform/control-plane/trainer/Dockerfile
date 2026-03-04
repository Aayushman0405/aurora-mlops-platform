FROM python:3.10-slim

WORKDIR /trainer

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy trainer script
COPY train.py .

# Create models directory
RUN mkdir -p /models

CMD ["python", "train.py"]
