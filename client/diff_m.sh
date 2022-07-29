#!/bin/bash

# Program:
# 	diffmonitor      
# History:
# 	2020/07/15	caishunzhi	First release
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

DIR=$(cd "$(dirname "$0")"; pwd)
LOG=$DIR/log
sleep ${RANDOM: -1}
CURL="curl -s --connect-timeout 30"
[ -n "$1" ] && SERVER=$1 || { echo "Please enter server address!!"; exit 1; }
API="http://$SERVER/api"
HOSTNAME=${2:-$HOSTNAME}
IP=${3:-127.0.0.1}

[ -d $DIR/tmp ] || mkdir -p $DIR/tmp
#log
log()
{
	echo "`date '+%F %T'`   $1" >>$LOG
}

[ -f $DIR/list.conf ] || { log "error!! list.conf does not exist!!"; exit 1; }

#ops
ops() 
{
	if [ $2 == "file" ];then
		[ -f $3 ] || { log "error!! file $3 does not exist!!"; continue; }
		md5=$(md5sum $3 |awk '{print $1}')
		content="$3"
	elif [ $2 == "shell" ];then
		[ -f $DIR/shell/$3 ] || { log "error!! shell $3 does not exist!!"; continue; }
		sh $DIR/shell/$3 >$DIR/shell/z_${1} 2>>$LOG
		[ $? -eq 0 ] || { echo "shell $3 error, please check!"; continue; }
		md5=$(md5sum $DIR/shell/z_${1} |awk '{print $1}')
		content="$DIR/shell/z_${1}"
	fi

	oldmd5=`$CURL $API/md5 -d hostname="$HOSTNAME" -d type="$1" -d md5="$md5"`
	if [ $? -eq 0 ];then
		log "oldmd5=$oldmd5 newmd5=$md5 $1"
	else
		log "get oldmd5 failed $1"
		continue
	fi

	if [ "$oldmd5" == "status_no_ok" ];then
		continue
	elif [ "$oldmd5" == "null" ];then
		$CURL $API/create -d hostname="$HOSTNAME" -d ip="$IP" -d type="$1" -d md5="$md5" --data-urlencode content="`cat $content`"
		[ $? -eq 0 ] && log "create $HOSTNAME $1 success" || log "create $HOSTNAME $1 failed"
		continue
	elif [ "$oldmd5" != "$md5" ];then
		$CURL $API/content -d hostname="$HOSTNAME" -d type="$1" >$DIR/tmp/${1}.tmp
		sed -i -e '$a\' $DIR/tmp/${1}.tmp
		DIFFCONTENT=$(diff $DIR/tmp/${1}.tmp $content)
		$CURL $API/update -d hostname="$HOSTNAME" -d type="$1" -d newmd5="$md5" --data-urlencode newcontent="`cat $content`" --data-urlencode diff="$DIFFCONTENT";
		[ $? -eq 0 ] && log "update $HOSTNAME $1 success" || log "update $HOSTNAME $1 failed"
	fi
}

cat $DIR/list.conf |grep -v "^#" |while read name type action;
do
	sleep 1
	ops $name $type $action
done

echo "" >>$LOG
