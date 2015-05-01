FROM python:2.7
MAINTAINER Peter Klausing <peter_klausing@wh2.tu-dresden.de>


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


RUN pip install uwsgi

RUN addgroup --gid 9999 sipa && \
	adduser --uid 9999 --gid 9999 --disabled-password --gecos "Application" sipa

RUN mkdir /var/log/sipa && \
    chown sipa:sipa /var/log/sipa

ADD . /home/sipa/sipa

WORKDIR /home/sipa/sipa
RUN chown -R sipa:sipa /home/sipa/sipa

RUN pip install -r requirements.txt


EXPOSE 5000

USER sipa
CMD ["/home/sipa/sipa/start.sh"]
