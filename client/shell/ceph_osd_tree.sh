#!/bin/bash

# Program:
#       
# History:
# 2021/02/07	caishunzhi	First release
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

timeout 10 ceph osd tree
