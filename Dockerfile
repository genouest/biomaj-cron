FROM debian:latest
MAINTAINER Olivier Sallou <olivier.sallou@irisa.fr>

RUN apt-get update && apt-get install -y cron git python3 python3-dev python3-pip

RUN git clone https://github.com/genouest/biomaj-cron.git

RUN cd biomaj-cron && python3 setup.py install

RUN git clone https://github.com/genouest/biomaj-cli.git

RUN cd biomaj-cli && python3 setup.py install


# Create the log file to be able to run tail
RUN touch /var/log/cron.log

COPY docker_start.sh /root/docker_start.sh
COPY config.yml /root/config.yml
ENV BIOMAJ_CONFIG=/root/config.yml
# Run the command on container startup
CMD /root/docker_start.sh
