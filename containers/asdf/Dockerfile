FROM ubuntu:20.04

COPY containers/asdf/init.sh /app/init.sh

RUN apt-get update && apt-get install -y openvswitch-switch


WORKDIR /app
CMD ["sleep", "1000000"]
# CMD ["/app/init.sh"]
# CMD ["/usr/sbin/ovs-vswitchd"]