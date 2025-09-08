FROM python:3.12
MAINTAINER Lukas Juhrich der Große <lukasjuhrich@wh2.tu-dresden.de>

ARG UID=9999
ARG GID=9999

ENV DEBIAN_FRONTEND=noninteractive \
	LC_ALL=C

RUN apt-get update && apt-get install -y --force-yes --no-install-recommends \
	libsasl2-dev \
	default-libmysqlclient-dev \
	libxml2-dev \
	libxslt1-dev \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
  && groupadd --force --gid $GID sipa \
    && useradd --non-unique --home-dir /opt/sipa --create-home --uid $UID --gid $GID --comment "Application" sipa

RUN curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.8.15/uv-installer.sh | sh \
    && mv $HOME/.local/bin/uv /usr/local/bin/

WORKDIR /opt/sipa

COPY --chown=sipa:sipa . /opt/sipa
RUN uv pip install --system . --group prod

EXPOSE 5000

USER sipa

CMD ["uwsgi", "--ini", "uwsgi.ini"]
