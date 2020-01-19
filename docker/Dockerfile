# docker build -t gitlab.lrz.de:5005/i7/dtcontrol:<num> .
# docker push gitlab.lrz.de:5005/i7/dtcontrol
# Update in .gitlab-ci.yml

# Run the create_docker_examples script before building a new docker image!

FROM alpine

COPY req.txt /req.txt

ENV PYTHONUNBUFFERED=1

# in the following, we need to manually install Cython and numpy because of some bug in pip/pandas where the install fails
RUN \
     apk add --update python3 libgfortran libgcc libstdc++ openblas linux-headers \
  && apk add --update --virtual .build build-base python3-dev openblas-dev freetype-dev pkgconfig gfortran \
  && python3 -mensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install --no-cache-dir Cython==0.29.14 \
  && pip3 install --no-cache-dir numpy==1.17.3 \
  && pip3 install --upgrade --no-cache-dir pip \
  && pip3 install --no-cache-dir -r /req.txt \
  && apk del .build \
  && rm /var/cache/apk/*
