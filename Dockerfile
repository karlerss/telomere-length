FROM biocontainers/biocontainers:latest
MAINTAINER Karl-Sander Erss <karl.erss@gmail.com>
RUN conda install -c bioconda sra-tools=2.8.1
ADD ./bin /usr/sbin
# cache deps
COPY ./tlenpy/requirements.txt /tlenpy/requirements.txt
WORKDIR /tlenpy
RUN pip install -r requirements.txt
COPY ./user-settings.mkfg /home/biodocker/.ncbi/user-settings.mkfg
COPY ./tlenpy /tlenpy
#RUN vdb-config -i
#RUN sed -i 'Ns/.*/replacement-line/' file.txt