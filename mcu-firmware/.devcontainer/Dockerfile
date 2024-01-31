FROM python:3.12-bullseye

WORKDIR /src

RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh ssh -T git@github.com

COPY tools/requirements.txt /tmp/pip-tmp/
RUN --mount=type=ssh pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp