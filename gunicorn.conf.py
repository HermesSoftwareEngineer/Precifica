# Gunicorn configuration file
import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:{}".format(os.environ.get("PORT", "5000"))
backlog = 2048

# Worker Processes
# Use gevent for async workers to handle long-running AI requests
worker_class = "gevent"
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000

# Timeout Configuration
# Extended timeout for AI/LLM processing (5 minutes)
timeout = 300
keepalive = 5

# Graceful timeout for shutdown
graceful_timeout = 30

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Process Naming
proc_name = "precifica_app"

# Preload app for better performance
# WARNING: preload_app=True is incompatible with gevent workers unless monkey patching is done
# before the app is loaded. This causes SSL/Socket errors (TypeError: super(type, obj)...).
# We disable it to ensure each worker loads the app in a fully patched environment.
preload_app = False

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None
