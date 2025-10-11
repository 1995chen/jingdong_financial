# 第一阶段: 构建Python环境
FROM ubuntu:22.04 as builder

ENV PATH="/opt/miniconda3/bin:$PATH"
RUN useradd -m appuser
# 拷贝配置文件以及依赖文件
COPY ./environment.yaml /opt/application/
# 安装conda
RUN apt-get update -y && apt-get install -y wget git gcc && \ 
    mkdir -p /opt/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/miniconda3/miniconda.sh && \
    bash /opt/miniconda3/miniconda.sh -b -u -p /opt/miniconda3  && \
    rm -rf /opt/miniconda3/miniconda.sh && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda env create -f /opt/application/environment.yaml && \ 
    conda clean -afy && \
    chown -R appuser:appuser /opt/miniconda3 && \
    cd /opt && tar -zcvf miniconda3.tgz miniconda3
# 第二阶段：仅复制最小化环境
FROM ubuntu:22.04
ENV PATH="/opt/miniconda3/envs/jingdong_financial/bin:$PATH"
ENV RUNTIME_ENV DEV
ENV PORT=8080
# 安装必要的系统包
RUN apt-get update -y && apt-get install -y \
    ffmpeg vim make logrotate syslog-ng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN useradd -m appuser
COPY docker/app.conf /etc/supervisor/conf.d/
COPY docker/supervisord.conf /etc/supervisor/
COPY docker/app /etc/logrotate.d/
COPY docker/syslog-ng.conf /etc/syslog-ng/
COPY ./ /opt/application/
# 拷贝python环境
COPY --from=builder --chown=appuser:appuser /opt/miniconda3.tgz /opt/miniconda3.tgz
RUN /usr/sbin/logrotate -f /etc/logrotate.conf && \
    mkdir -p /opt/application/logs /var/log/syslog-ng/ && \
    tar -zxf /opt/miniconda3.tgz -C /opt && rm -rf /opt/miniconda3.tgz && \
    chown -R appuser:appuser /opt/application /opt/miniconda3 /etc/syslog-ng/ /etc/logrotate.d/ /var/lib/syslog-ng/ /var/log/syslog-ng/
WORKDIR /opt/application
USER appuser
EXPOSE 8080
CMD ["bash", "-c", "supervisord -c /etc/supervisor/supervisord.conf" ]