FROM debian:bookworm-slim

ARG SPYSERVER_DOWNLOAD_URL=https://airspy.com/?ddownload=4262

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl librtlsdr-dev libusb-1.0-0 rtl-sdr tar tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN test -e /usr/lib/x86_64-linux-gnu/librtlsdr.so

WORKDIR /opt/spyserver
RUN curl -fsSL "$SPYSERVER_DOWNLOAD_URL" -o /tmp/spyserver.tgz \
    && tar -xzf /tmp/spyserver.tgz -C /opt/spyserver \
    && rm -f /tmp/spyserver.tgz \
    && chmod +x /opt/spyserver/spyserver

COPY spyserver/entrypoint.sh /usr/local/bin/spyserver-entrypoint.sh
RUN chmod +x /usr/local/bin/spyserver-entrypoint.sh

EXPOSE 5555/tcp

ENTRYPOINT ["/usr/local/bin/spyserver-entrypoint.sh"]
