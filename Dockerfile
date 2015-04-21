FROM phusion/baseimage
MAINTAINER Peter Klausing <peter_klausing@wh2.tu-dresden.de>

CMD ["/sbin/my_init"]

ENV DEBIAN_FRONTEND noninteractive 
ENV LC_ALL C

RUN apt-get update && \
    apt-get -y install --no-install-recommends  \
      python-dev \
      python-pip \
      python-wheel \
      build-essential \
      libmysqlclient-dev \ 
      libsasl2-dev \
      libldap2-dev \ 
      libffi-dev \
      libxml2-dev \ 
      libxslt1-dev
RUN pip install twine 
RUN pip install uwsgi

RUN addgroup --gid 9999 sipa
RUN adduser --uid 9999 --gid 9999 --disabled-password --gecos "Application" sipa
RUN usermod -L sipa

RUN mkdir /var/log/sipa
RUN chown sipa:sipa /var/log/sipa

ADD . /home/sipa/sipa

WORKDIR /home/sipa/sipa
RUN python /home/sipa/sipa/setup.py install

RUN mkdir /etc/service/sipa
ADD start.sh /etc/service/sipa/run

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 5000
