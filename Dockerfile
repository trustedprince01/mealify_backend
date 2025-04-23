# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Create start script
RUN echo '#!/bin/bash\n\
python manage.py migrate --noinput\n\
python manage.py collectstatic --noinput\n\
gunicorn mealify_backend.wsgi:application --bind 0.0.0.0:$PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start command
CMD ["/app/start.sh"]