FROM python:3.6-alpine

# install git
RUN apk add --no-cache git
# copy app to dockerfile
COPY . /app/watcher3

# ports and volumes
EXPOSE 9090
WORKDIR /app/watcher3
VOLUME /config /downloads /movies /app/watcher3/userdata

CMD python /app/watcher3/watcher.py -c /config/config.cfg -l /config/logs/ --db /config/database.sqlite --plugins /config/plugins/