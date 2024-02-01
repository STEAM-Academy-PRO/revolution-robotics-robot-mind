FROM python:3.12-bullseye

WORKDIR /src

RUN mkdir gcc-arm \
    && cd gcc-arm \
    && wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2 -O toolchain.tar.bz2 \
    && tar -xjf toolchain.tar.bz2 \
    && rm -rf toolchain.tar.bz2 \
    && echo "export PATH=/src/gcc-arm/gcc-arm-none-eabi-10.3-2021.10/bin:$PATH" >> ~/.bashrc

ENV IN_CONTAINER=1

RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

COPY tools/requirements.txt /tmp/pip-tmp/
RUN --mount=type=ssh pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp