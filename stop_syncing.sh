#!/bin/bash

LOG_DIR=/var/log/samba_sync

if [ ! -d $LOG_DIR ]; then
	mkdir -p $LOG_DIR;
fi

samba-tool user syncpasswords --terminate \
    --logfile=$LOG_DIR/user-syncpasswords.log

