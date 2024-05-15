#!/bin/bash

COUNT=0
echo $COUNT > ./uploads-count
while [ ! -f ./stopfile ];
  do echo -e "HTTP/1.1 200 OK\n\n$(echo Success!)" \
  | nc -l -k -p 8080 -q 1 | grep '' && (echo Upload received!; COUNT=$((COUNT+1)) > /dev/null);
done

echo $COUNT | tee ./uploads-count

echo Shutting down bash-srv

exit 0