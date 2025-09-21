FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Poetry
# We use a multi-stage approach or a single command to install Poetry
RUN pip install poetry

RUN poetry self add poetry-plugin-export

# Copy the Poetry files to the container
COPY pyproject.toml poetry.lock ./

RUN poetry export --without-hashes --format=requirements.txt > requirements.txt

RUN pip install -r /app/requirements.txt

RUN pip install uwsgi

# Copy the application source code
COPY ./app.py .

# Expose the port the app runs on
EXPOSE 3000

CMD ["uwsgi", "--ini", "/app/wsgi.ini"]
