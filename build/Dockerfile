FROM python:latest
MAINTAINER Lukas Juhrich der Große <lukasjuhrich@wh2.tu-dresden.de>


ENV DEBIAN_FRONTEND=noninteractive \
	LC_ALL=C

RUN apt-get update && apt-get install -y --no-install-recommends \
	libldap2-dev \
	libsasl2-dev \
	libmysqlclient-dev \
	libxml2-dev \
	libxslt1-dev \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --upgrade pip

RUN pip install uwsgi

RUN addgroup --gid 9999 sipa && \
	adduser --uid 9999 --gid 9999 --disabled-password --gecos "Application" sipa

RUN mkdir /home/sipa/sipa
WORKDIR /home/sipa/sipa

ADD ./build /home/sipa/sipa/build/
ARG additional_requirements
RUN ./build/install_requirements.py $additional_requirements

ADD . /home/sipa/sipa
RUN chown -R sipa:sipa /home/sipa/sipa

EXPOSE 5000

USER sipa

CMD ["uwsgi", "--ini", "uwsgi.ini"]