FROM ubuntu:16.04

RUN  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections

#install java 8
RUN  apt-get update
RUN  apt-get install -y software-properties-common
RUN  add-apt-repository -y ppa:webupd8team/java
RUN  apt-get update
RUN  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

#copied from continuums docker image. Also install scala
RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion scala

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/archive/Anaconda3-4.2.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh


ENV PATH /opt/conda/bin:$PATH

# Add Tini
ENV TINI_VERSION v0.13.2
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

# add ctapipe
RUN conda install -y ctapipe -c cta-observatory

#add spark stuff. we use messagepack to serialize objects to kafka.
#quite horrible isn't it?
RUN pip install py4j pykafka msgpack-python msgpack-numpy && \
    wget --quiet http://d3kbcqa49mib13.cloudfront.net/spark-2.1.0-bin-hadoop2.7.tgz && \
    tar -xzf spark-2.1.0-bin-hadoop2.7.tgz && \
    mv spark-2.1.0-bin-hadoop2.7 spark && \
    rm spark-2.1.0-bin-hadoop2.7.tgz

ENV SPARK_HOME /spark
#I know this is ugly. but seems to work
ENV PYTHONPATH /spark/python

EXPOSE 5555 8080 7077 9080 9081 57600 7600 8181 9990 4040 55200 45700 8081

ADD ./scripts/ /scripts

CMD [ "/bin/bash" ]
#now you can  try something like: python spark/examples/src/main/python/pi.py
