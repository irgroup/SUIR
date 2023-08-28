FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
	git \
	openjdk-17-jdk \
	openjdk-17-jre \
	postgresql-client \
	libgomp1

WORKDIR /workspace
ADD . /workspace

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install --upgrade git+https://github.com/terrier-org/pyterrier.git#egg=python-terrier
                                        
RUN pip install -U pip setuptools wheel

