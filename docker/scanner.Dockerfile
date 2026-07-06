FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends rtl-sdr ca-certificates bash tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY scanner/scan_loop.sh /usr/local/bin/scan_loop.sh
RUN chmod +x /usr/local/bin/scan_loop.sh

CMD ["/usr/local/bin/scan_loop.sh"]
