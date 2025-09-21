FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Poetry
# We use a multi-stage approach or a single command to install Poetry
RUN pip install poetry

# Copy the Poetry files to the container
COPY pyproject.toml poetry.lock ./

# Install project dependencies
# The --no-root flag ensures that the package itself isn't installed
# in editable mode inside the container.
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the application source code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application with Poetry
CMD ["poetry", "run", "python", "app.py"]
