FROM python:3-alpine

# Note that git is not uninstalled later, as it's needed for the
#  installation of the requirements.
RUN apk add --no-cache gcc libressl-dev musl-dev libffi-dev git && \
    pip install cryptography && \
    apk del gcc libressl-dev  musl-dev libffi-dev

ADD . /app
RUN pip install -r /app/requirements.txt && pip install -e /app

# Bridge database (registrations, chatrooms, ...)
VOLUME /root/.local/share/plaza/bridges/telegram/db.sqlite

CMD plaza-telegram-service
