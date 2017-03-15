FROM alpine:3.5

ADD . /app
WORKDIR /app

MAINTAINER Christoph Gerneth <christoph@gerneth.info>

ENV FLASK_APP server.py
ENV MAIL_SERVER mail.one.com
ENV MAIL_PORT 25
ENV MAIL_USE_TLS  False
ENV MAIL_USE_SSL False
ENV MAIL_USERNAME usernamehere
ENV MAIL_PASSWORD passwordhere
ENV DATABASE_URI 'sqlite:////tmp/database.db'

RUN apk --no-cache add --virtual build-deps build-base python3-dev curl netcat-openbsd \
 && apk --no-cache add --virtual runtime-deps python3 libpq ca-certificates \
 && apk --no-cache upgrade \
 && curl -O https://bootstrap.pypa.io/get-pip.py \
 && python3 get-pip.py \
 && pip3 install -r requirements.txt \
 && apk del --purge build-deps \
 && python3 bootstrap.py

ENTRYPOINT ["python"]

CMD ["flask run"]