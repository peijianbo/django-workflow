#!/bin/bash
# !!! 需要先手工login hub

docker build -f docker_files/Dockerfile -t workflow:1.0.0 .
# 重命名镜像
docker tag workflow:1.0.0 jianbopei/workflow:1.0.1
# 推送镜像
docker push jianbopei/workflow:1.0.1
