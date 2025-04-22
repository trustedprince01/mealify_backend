# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG=True
ENV SECRET_KEY=temporary-key-for-build-only
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Print directory structure for debugging
RUN ls -la

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Debug - check if api directory exists
RUN echo "Directory listing after copy:" && ls -la && echo "API directory:" && ls -la api

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Start command
CMD python manage.py collectstatic --noinput && gunicorn mealify_backend.wsgi --log-file -