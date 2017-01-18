FROM ubuntu:16.04

RUN  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections 

RUN  apt-get update 
RUN  apt-get install -y software-properties-common 
RUN  add-apt-repository -y ppa:webupd8team/java
RUN  apt-get update
RUN  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

#copied from 
RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/archive/Anaconda2-4.2.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh


ENV PATH /opt/conda/bin:$PATH

# Add Tini
ENV TINI_VERSION v0.13.2
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

# add scientific things
RUN conda install -y scipy matplotlib astropy pandas 

# add ctapipe things
RUN conda install -y ctapipe -c cta-observatory

#add spark things
RUN pip install --yes py4j

#add kafka things
RUN pip install --yes pykafka

CMD [ "/bin/bash" ]
