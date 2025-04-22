# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG=True
ENV SECRET_KEY=temporary-key-for-build-only

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Start command - collectstatic at runtime not build time
CMD python manage.py collectstatic --noinput && gunicorn mealify_backend.wsgi --log-file -