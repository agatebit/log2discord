#!/bin/bash

echo Found "$(cat ./uploads-count)" of "$SUCCESSFUL_UPLOADS"

if [ "$(cat ./uploads-count)" -eq "$SUCCESSFUL_UPLOADS" ]
then
  exit 0
fi
exit 1