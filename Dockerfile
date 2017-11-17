FROM python:3.6-alpine
LABEL author="guysp"

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Version:- ${VERSION} Build-date:- ${BUILD_DATE}"

# install git
RUN apk add --no-cache git
# copy app to dockerfile
COPY . /app/watcher3

# ports and volumes
EXPOSE 9090
WORKDIR /app/watcher3
VOLUME /config /downloads /movies

CMD python /app/watcher3/watcher.py -c /config/config.cfg -l /config/logs/ --db /config/database.sqlite --plugins /config/plugins/