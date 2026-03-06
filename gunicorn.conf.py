# Gunicorn configuration for memory-constrained environments
import multiprocessing
import os

# Gunicorn configuration optimized for Cloud Run
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1  # Single worker to reduce memory
threads = 4  # Use threads for concurrency
worker_class = 'gthread'  # Thread-based worker
timeout = 300  # 5 minute timeout for file processing
keepalive = 5
max_requests = 200  # Restart worker periodically to prevent memory leaks
max_requests_jitter = 50
worker_tmp_dir = '/dev/shm'  # Use RAM disk for temp files

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Preload app (set to False to save memory)
preload_app = False