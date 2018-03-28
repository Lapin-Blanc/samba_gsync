#!/usr/bin/env python
import os
import sys
import re
import logging
import httplib2
import json

from apiclient import discovery
from ggl.credentials import get_credentials

log_dir = "/var/log/samba_sync"
working_dir = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir,'sync.log'),level=logging.DEBUG)

config = json.load(open(os.path.join(working_dir, 'config.json')))
DOMAIN = config['domain']

BUILD_DICT = {
    "name": {
        "familyName": "",
        "givenName": "",
    },
    "password": "",
    "primaryEmail": "",
    "hashFunction": "crypt"
}

UPDATE_DICT = {
    "name": {
        "familyName": "",
        "givenName": "",
    },
    "hashFunction": "crypt",
    "password": ""
}

cred = get_credentials()

logging.warning("============== Sync script start ==================")
# logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

# Google directory service
http = cred.authorize(httplib2.Http())
service = discovery.build('admin', 'directory_v1', http=http, cache_discovery=False)
logging.info("Google service instanciated")

# Raw user list
users = service.users().list(customer="my_customer").execute()['users']
# List of existing users (emails)
g_users = [u['primaryEmail'] for u in users]
logging.info("Google user list retrieved {}".format(g_users))

# Parsing stdin as ldif
data = []
for line in sys.stdin.readlines():
    match = re.match( '^ (.*\n)', line )
    # Check if line begins with a space, join with last line
    if match:
    # Found line beginning with space, joining with last line"
        # Pop last line and remove line return
        lastline = re.sub( '(.*)\n', '\\1', data.pop() )
        # Join result with current line without space
        newline = lastline + match.group(1)
        data.append( newline )
    # Normal line
    else:
        data.append( line )

# Looping through all lines and detect DN and attributes
# building a dict with diff's attibutes and values
data_dict = {}
for line in data:
    # Test if we have a typical LDIF line "xxx: yyy"
    match = re.match( '^(.*?): (.*)\n', line )
    if match:
        # If xxx is a dn
        if match.group(1) == "dn":
            logging.info("DN found: {}".format( match.group(2) ))
        # If xxx is an attribute meaning no changetype or add or replace or delete
        elif not re.match( 'version|changetype|add|replace|delete', match.group(1) ):
            k = match.group(1)
            val = match.group(2)
            logging.info("Attribute found: {} = {}".format( k, val ))
            data_dict[k] = val

account_name = data_dict.get("sAMAccountName", None)
if (account_name):
    primaryEmail = account_name + "@" + DOMAIN
    # if no givenName, we use account_name
    givenName = data_dict.get('givenName', account_name)
    # if no familyName, we use account_name
    familyName = data_dict.get('sn', account_name)

passwd = data_dict.get("virtualCryptSHA512", False)
if (passwd):
    match = re.match("^\{CRYPT\}(.*)$", passwd)
    passwd = match.group(1)

deleted = data_dict.get("isDeleted", False)
if deleted:
    deleted = data_dict.get("isDeleted") == 'TRUE'

# real user, either with password or planned for deletion
if ( account_name and (passwd or deleted) ):
	# user to delete exists in the google domain
    if ( deleted and (primaryEmail in g_users) ):
        logging.info("User {} is about to be deleted...".format(primaryEmail))
        results = service.users().delete( userKey=primaryEmail ).execute()
        logging.info(results)
        logging.warning("User {} deleted !".format(primaryEmail))
    # we have to make sure this is not a localy only deletion
    elif ( not deleted ):
        if ( primaryEmail in g_users ):
            logging.info("User {} already present, updating password...".format(primaryEmail))
            UPDATE_DICT["password"] = passwd
            UPDATE_DICT['name']['givenName'] = givenName
            UPDATE_DICT['name']['familyName'] = familyName
            results = service.users().update(userKey=primaryEmail, body=UPDATE_DICT).execute()
            logging.info(results)
            logging.warning("Password updated for {} !".format(primaryEmail))
        else:
            BUILD_DICT['primaryEmail'] = primaryEmail
            BUILD_DICT['name']['givenName'] = givenName
            BUILD_DICT['name']['familyName'] = familyName
            BUILD_DICT['password'] = passwd
            logging.info("Creating user {}...".format(primaryEmail))
            results = service.users().insert(body=BUILD_DICT).execute()
            logging.info(results)
            logging.warning("User {} created !".format(primaryEmail))

logging.warning("============== Sync script end ==================")

# needed for the sync script to end gracefully
print('DONE-EXIT: processed {} !'.format(account_name))
