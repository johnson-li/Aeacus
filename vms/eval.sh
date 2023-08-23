#!/bin/bash

ssh -F tmp/ssh-config ue '~/bin/http3-client -u https://a.ns7.xuebing.online -a 192.168.57.12'
