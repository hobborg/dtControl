# docker build -t gitlab.lrz.de:5005/i7/dtcontrol:<num> .
# docker push gitlab.lrz.de:5005/i7/dtcontrol
# Update in .gitlab-ci.yml

# Run the create_docker_examples script before building a new docker image!

FROM ubuntu:rolling

COPY req.txt /req.txt

ENV PYTHONUNBUFFERED=1

# in the following, we need to manually install Cython and numpy because of some bug in pip/pandas where the install fails
RUN \
  apt-get update && apt-get install -y \
  git \
  python3.7 \
  python3.8 \
  python3.7-dev \
  python3.8-dev \
  python3-pip \
  ssh \ 
  && python3.7 -m pip install --no-cache-dir -r /req.txt \
  && python3.8 -m pip install --no-cache-dir -r /req.txt \
  && apt-get remove -y python3.7-dev python3.8-dev \
  && apt-get -y autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
