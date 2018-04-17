#!/bin/bash

SCRIPT_DIR=/usr/local/samba_gsync
CACHE_FILE=/usr/local/samba/private/user-syncpasswords-cache.ldb
LOG_DIR=/var/log/samba_sync
SAMBA_DIR=/usr/local/samba

# rm /usr/local/samba/private/user-syncpasswords-cache.ldb
if [ ! -f $CACHE_FILE ]; then
    echo "Cache not yet initiated..."
	$SAMBA_DIR/bin/samba-tool user syncpasswords --cache-ldb-initialize \
		--attributes=objectGUID,objectSID,sAMAccountName,userPrincipalName,userAccountControl,pwdLastSet,msDS-KeyVersionNumber,virtualCryptSHA512,cn,sn,givenName,name,displayName \
		--script=$SCRIPT_DIR/sync.py
    echo "Done !";
fi

if [ ! -d $LOG_DIR ]; then
	mkdir -p $LOG_DIR;
fi

$SAMBA_DIR/bin/samba-tool user syncpasswords --daemon \
    --logfile=$LOG_DIR/user-syncpasswords.log
