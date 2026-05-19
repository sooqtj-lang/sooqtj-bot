FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build mini-app
COPY mini-app/package.json mini-app/package-lock.json* ./mini-app/
RUN cd mini-app && npm install

COPY mini-app/ ./mini-app/
RUN cd mini-app && npm run build

# Copy rest of app
COPY . .

EXPOSE 8080
CMD uvicorn api:app --host 0.0.0.0 --port $PORT
