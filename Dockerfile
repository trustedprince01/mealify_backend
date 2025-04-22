# Use Python 3.9 image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files and run migrations during container start
CMD python manage.py collectstatic --noinput && python manage.py migrate && gunicorn mealify_backend.wsgi:application --bind 0.0.0.0:$PORT