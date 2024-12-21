# Gunicorn configuration file
import multiprocessing

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = 'uvicorn.workers.UvicornWorker'

# Timeout for worker processes
timeout = 600

# Keep-alive timeout
keepalive = 5

# Maximum number of requests a worker will process before restarting
max_requests = 1000

# Maximum jitter to add to the max_requests setting
max_requests_jitter = 50

# Log level
loglevel = 'info'

# Access log - "-" means log to stdout
accesslog = '-'

# Error log - "-" means log to stdout
errorlog = '-'

# Preload application code before worker processes are forked
preload_app = True