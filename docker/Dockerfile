FROM ubuntu:22.04
MAINTAINER liang.chen

RUN apt-get update -y && apt-get install -y \
    ffmpeg vim make logrotate wget && \
    rm -rf /var/lib/apt/lists/*
# 安装conda并软链
RUN mkdir -p /opt/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/miniconda3/miniconda.sh && \
    bash /opt/miniconda3/miniconda.sh -b -u -p /opt/miniconda3  && \
    rm -rf /opt/miniconda3/miniconda.sh && \
    source /opt/miniconda3/bin/activate && \
    conda init --all && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda env create -f environment.yaml
# 拷贝配置文件
COPY docker/app.conf /etc/supervisor/conf.d/
# 拷贝日志文件配置
COPY docker/app /etc/logrotate.d/
RUN /usr/sbin/logrotate -f /etc/logrotate.conf

# 默认的环境变量
ENV PATH="/opt/miniconda3/envs/jingdong_financial/bin:$PATH"
ENV RUNTIME_ENV DEV
ENV PORT=8080

WORKDIR /opt/application
# 拷贝代码
COPY ./ /opt/application/

RUN mkdir -p /opt/application/logs
CMD ["bash", "-c", "/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf"]
