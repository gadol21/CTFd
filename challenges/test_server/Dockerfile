FROM alpine:latest
RUN apk update && \
    apk add python

# Assume this is already mapped
WORKDIR /root/challenge

EXPOSE 3260

ENTRYPOINT ["python", "main.py"]
