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
  && pip install --upgrade pip \
  && pip install uwsgi \
  && groupadd --force --gid $GID sipa \
    && useradd --non-unique --home-dir /opt/sipa --create-home --uid $UID --gid $GID --comment "Application" sipa

WORKDIR /opt/sipa

COPY --chown=sipa:sipa ./build /opt/sipa/build/
COPY --chown=sipa:sipa ./wtforms_widgets /opt/sipa/wtforms_widgets
ARG additional_requirements
RUN ./build/install_requirements.py $additional_requirements

COPY --chown=sipa:sipa . /opt/sipa

EXPOSE 5000

USER sipa

CMD ["uwsgi", "--ini", "uwsgi.ini"]
