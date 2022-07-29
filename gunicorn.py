# 并行工作进程数
workers = 4
# 指定每个工作者的线程数
threads = 2
# 监听内网端口5000
bind = '0.0.0.0:5000'
# 设置守护进程
daemon = 'false'
# 工作模式协程
# worker_class = 'gevent'
# 设置最大并发量
worker_connections = 2000
# 设置进程文件目录
pidfile = '/var/run/gunicorn.pid'
# 设置访问日志和错误信息日志路径
accesslog = './log/access.log'
errorlog = './log/error.log'
# 设置这个值为true 才会把打印信息记录到错误日志里
capture_output = True
# 设置日志记录水平
loglevel = 'info'