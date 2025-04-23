# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Start command
CMD python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mealify_backend.wsgi:application --bind 0.0.0.0:$PORT