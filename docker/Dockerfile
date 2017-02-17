FROM centos:centos7

RUN yum install -y gcc make git openssl-devel sqlite-devel bzip2-devel gdbm-devel xz-devel readline-devel

WORKDIR /opt

RUN mkdir database \
    && cd database \
    && curl -O https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel70-3.4.1.tgz \
    && tar -zxf mongodb-linux-x86_64-rhel70-3.4.1.tgz \
    && mkdir -p /data/db

RUN curl -O https://www.python.org/ftp/python/3.4.5/Python-3.4.5.tgz \
    && tar -zxf Python-3.4.5.tgz \
    && rm Python-3.4.5.tgz \
    && cd Python-3.4.5 \
    && ./configure --prefix=$(pwd) > configure.log \
    && make > make.log \
    && make altinstall > install.log \
    && cd .. \
    && Python-3.4.5/bin/pyvenv-3.4 ./python

RUN curl -O https://ftp.postgresql.org/pub/source/v9.6.1/postgresql-9.6.1.tar.gz \
    && tar -zxf postgresql-9.6.1.tar.gz \
    && rm postgresql-9.6.1.tar.gz \
    && cd postgresql-9.6.1 \
    && ./configure --prefix=$(pwd) --without-readline > configure.log \
    && make > make.log \
    && make install > install.log

RUN git clone https://github.com/EdinburghGenomics/Reporting-App.git \
    && cd Reporting-App \
    && PATH=$PATH:/opt/postgresql-9.6.1/bin /opt/python/bin/pip install -q -r requirements.txt \
    && /opt/python/bin/pip install tornado

ADD reporting.yaml /opt/reporting.yaml

RUN REPORTINGCONFIG=/opt/reporting.yaml \
    /opt/python/bin/python \
    /opt/Reporting-App/auth.py add apiuser

VOLUME /data/db

EXPOSE 4999

CMD /opt/database/mongodb-linux-x86_64-rhel70-3.4.1/bin/mongod --port 4998 > /opt/database/mongod.log & \
    REPORTINGCONFIG=/opt/reporting.yaml /opt/python/bin/python /opt/Reporting-App/bin/run_app.py rest_api
