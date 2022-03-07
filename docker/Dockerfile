FROM 1995chen/python:3.6.8-dcf3637
MAINTAINER liang.chen

# 拷贝配置文件
COPY docker/app.conf /etc/supervisor/conf.d/
# 拷贝日志文件配置
COPY docker/app /etc/logrotate.d/
RUN /usr/sbin/logrotate -f /etc/logrotate.conf

# 默认的环境变量
ENV RUNTIME_ENV DEV
ENV PORT=8080

# 安装依赖,此步骤提前可以利用docker缓存加速
WORKDIR /opt/application
ADD ./requirements.txt /opt/application/requirements.txt
RUN pip3 install --timeout 100 --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

# 拷贝代码
COPY ./ /opt/application/

RUN mkdir -p /opt/application/logs
CMD ["bash", "-c", "/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf"]
