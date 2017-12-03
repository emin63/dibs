
FROM ubuntu:16.04
ENV DEBIAN_FRONTEND noninteractive

# Note that if the build fails, you main need to try a build with --no-cache

# Need to do an apt-get update early on or lots of things won't work.
RUN apt-get update

RUN apt-get -y install python3 python3-pip

CMD sleep 1000000