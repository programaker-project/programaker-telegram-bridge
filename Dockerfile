FROM python:3-alpine

# Note that everything is uninstalled later.
ADD requirements.txt /app/requirements.txt
RUN apk add --no-cache git libpq postgresql-dev build-base libressl-dev libffi-dev \
  && pip install -r /app/requirements.txt \
  && apk del git build-base postgresql-dev libressl-dev libffi-dev

ADD . /app
RUN pip install -e /app

# Bridge database (registrations, chatrooms, ...)
VOLUME /root/.local/share/plaza/bridges/telegram/db.sqlite

CMD plaza-telegram-service
