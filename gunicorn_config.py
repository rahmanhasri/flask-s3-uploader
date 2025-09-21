# gunicorn_config.py
workers = 4 # Number of worker processes
threads = 2 # Number of threads per worker
bind = "0.0.0.0:8000" # Address and port to bind to
timeout = 30 # Worker timeout in seconds