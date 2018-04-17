#!/bin/bash

LOG_DIR=/var/log/samba_sync
SAMBA_DIR=/usr/local/samba

if [ ! -d $LOG_DIR ]; then
	mkdir -p $LOG_DIR;
fi

$SAMBA_DIR/bin/samba-tool user syncpasswords --terminate \
    --logfile=$LOG_DIR/user-syncpasswords.log

