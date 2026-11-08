import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
timeout = 60
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 50
