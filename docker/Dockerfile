FROM ubuntu:22.04
MAINTAINER liang.chen

ENV PATH="/opt/miniconda3/bin:/opt/miniconda3/envs/jingdong_financial/bin:$PATH"
ENV RUNTIME_ENV DEV
ENV PORT=8080

RUN apt-get update -y && apt-get install -y \
    ffmpeg vim make logrotate wget git gcc syslog-ng && \
    rm -rf /var/lib/apt/lists/*

# 安装conda并软链
RUN mkdir -p /opt/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/miniconda3/miniconda.sh && \
    bash /opt/miniconda3/miniconda.sh -b -u -p /opt/miniconda3  && \
    rm -rf /opt/miniconda3/miniconda.sh && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# 拷贝配置文件
COPY docker/app.conf /etc/supervisor/conf.d/
COPY docker/supervisord.conf /etc/supervisor/
# 拷贝日志文件配置
COPY docker/app /etc/logrotate.d/
RUN /usr/sbin/logrotate -f /etc/logrotate.conf
COPY ./environment.yaml /opt/application/
RUN conda env create -f /opt/application/environment.yaml
WORKDIR /opt/application
# 拷贝代码
COPY ./ /opt/application/

RUN mkdir -p /opt/application/logs
CMD ["bash", "-c", "supervisord -c /etc/supervisor/supervisord.conf"]
