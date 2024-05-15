#!/bin/bash

send () {
	while IFS= read -r i; 
	#export HOSTNAME=`hostname`
	#echo $@
	do curl -X 'POST' $URL \
	 -H 'content-type: application/json' --output - \
	 -H 'accept: */*' -H 'accept-encoding: gzip, deflate' \
	 -H 'host: discord.com' \
	 -d '{"content": "", "embeds": [{"title": "WRAPPER: **Critical** error on '$HOSTNAME'!", "description": "```'"$i"'```\n<@800397602958709>, <@181730729483750183>, @here, @everyone", "color": 13191007, "footer": {"text": "'$HOSTNAME'", "timestamp": "'$(date --iso-8601=seconds)'"}}], "username": "'$HOSTNAME' log monitor wrapper script", "allowed_mentions": {"parse": ["everyone", "users"]}}' ;
	done;
}

export -f send

URL=$(grep url: ./config.yml | awk '{print $2}') || URL=$(grep url: ./config.yaml | awk '{print $2}' || echo ERROR!) || echo Unable to find webhook URL!
echo $URL

if [ "$SERVERLOGMONITORTEST" = "true" ];
then
	echo Entering test mode
	python3 main.py;
	EXITCODE=$?
	echo Python exited with code $EXITCODE
	exit $EXITCODE
fi

echo Entering production mode
while true;

do ( python3 main.py ) |& send
echo Restarting python | send
sleep 10;

done
