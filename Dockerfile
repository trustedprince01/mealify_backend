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

# Copy project files
COPY . .

# Debug - show directory listing
RUN echo "Directory listing:" && ls -la

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories (including api if it doesn't exist)
RUN mkdir -p staticfiles
RUN mkdir -p api
RUN touch api/__init__.py

# Expose port
EXPOSE 8000

# Start command
CMD python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mealify_backend.wsgi --log-file -