FROM debian:latest
LABEL authors="alex"

VOLUME /data
WORKDIR /data
RUN apt update && apt upgrade

RUN apt install openssl

ENTRYPOINT ["sh", "-c", "openssl req -x509 -nodes -days 3650 -newkey rsa:4096 -keyout priv.key -out cert.crt -subj /CN=AGDSN_Test && cat priv.key cert.crt > server.pem"]
