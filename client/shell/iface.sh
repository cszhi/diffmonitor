#!/bin/bash

# Program:
#       
# History:
# 2020/07/15	caishunzhi	First release
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

DEVICE=`ls -l /sys/class/net |grep devices|grep -v "virtual" |awk -F'/' '{print $NF}' |tr '\n' '|'`
mDEVICE="${DEVICE}bond"

ip a |grep "^[[:digit:]]" |grep -E $mDEVICE |grep -v " vif" |awk -F: '{print $2":"$3}' |sort
