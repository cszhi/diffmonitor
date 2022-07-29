FROM python:3.10.5-alpine
COPY ./diffmonitor /app

WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
EXPOSE 5000
ENTRYPOINT [ "gunicorn","-c","gunicorn.py","diffmonitor:app"]