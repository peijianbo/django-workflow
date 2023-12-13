FROM jianbopei/python38:latest

LABEL maintainer="peijianbo <peijianbo@tuyoogame.com>"
LABEL description="workflow-backend"

WORKDIR /data/server/workflow
COPY docker_files/run /data/server/run
COPY docker_files/requirements.txt /data/server/
COPY workflow /data/server/workflow

RUN pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --default-timeout=60 --no-cache-dir -r /data/server/requirements.txt


EXPOSE 8000

CMD ["sh","/data/server/run/start.sh"]
