FROM python:3.8.5-slim as builder
ENV DIR=/root/wechat
WORKDIR $DIR
COPY requirements.txt $DIR
COPY run.py $DIR
COPY util.py $DIR
RUN ls && \
# sed -i "s@http://deb.debian.org@https://mirrors.ustc.edu.cn@g" /etc/apt/sources.list && \
apt-get update && \
apt-get install -y binutils && \
# -i https://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com/pypi/simple/
pip3 install -r requirements.txt
RUN pyinstaller -F run.py --distpath . --add-data /usr/local/lib/python3.8/site-packages/pyecharts/datasets:pyecharts/datasets --add-data=/usr/local/lib/python3.8/site-packages/pyecharts/render/templates:pyecharts/render/templates --add-data=/usr/local/lib/python3.8/site-packages/jieba/dict.txt:jieba


FROM debian:stable-slim as runer
ENV DIR=/root/wechat
WORKDIR $DIR
COPY --from=0 $DIR/run $DIR
CMD ./run