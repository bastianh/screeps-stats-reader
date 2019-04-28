FROM python:3.6

RUN mkdir -p /home/deploy; \
    groupadd -g 1006 deploy; \
    useradd  -g 1006 -u 1006 deploy; \
    chown deploy.deploy /home/deploy

RUN pip3 install pipenv

RUN set -ex && mkdir /app

WORKDIR /app

# -- Adding Pipfiles
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# -- Install dependencies:
RUN set -ex && pipenv install --deploy --system

COPY src /app

USER deploy

ENTRYPOINT python ./stats.py