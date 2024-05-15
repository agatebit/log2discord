#!/bin/bash

awk '{print $0; system("sleep 1");}' ./tests/log-sample

sleep 5

touch ./stop-srv

sleep 5

exit 0
