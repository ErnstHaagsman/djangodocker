bind = 'unix:/tmp/gunicorn.sock'
workers = 4
errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(L)s %(s)s %(b)s "%(f)s" "%(a)s"'
