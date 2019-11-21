FROM alpine

COPY req.txt /req.txt

ENV PYTHONUNBUFFERED=1

RUN \
     apk add --update python3 libgfortran libgcc libstdc++ openblas linux-headers \
  && apk add --update --virtual .build build-base python3-dev openblas-dev freetype-dev pkgconfig gfortran \
  && python3 -mensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install --upgrade --no-cache-dir pip \
  && pip3 install --no-cache-dir -r /req.txt \
  && apk del .build \
  && rm /var/cache/apk/*

