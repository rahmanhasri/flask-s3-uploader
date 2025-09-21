FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only dependency files first
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-dev

RUN poetry install uwsgi

# Copy the application source code
COPY ./app.py ./wsgi.py ./uwsgi.ini ./

# Create a non-root user and switch to it
RUN useradd -m uploader && chown -R uploader:uploader /app
USER uploader

# Expose the port the app runs on
EXPOSE 5000

# Start uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]
