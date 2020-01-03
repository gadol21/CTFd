FROM ubuntu:latest
RUN apt update && \
    apt install -y socat

# Assume this is already mapped
WORKDIR /root/challenge

EXPOSE 3261

ENTRYPOINT ["/bin/sh", "socat.sh"]
