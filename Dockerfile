FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Render assigns a dynamic port via the PORT environment variable
# We default to 8000 for local development
ENV PORT=8000
EXPOSE $PORT

# Start the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
