#!/usr/bin/env python
import os
import sys
import logging
import httplib2
import json
import re
from ldif3 import LDIFParser

from apiclient import discovery
from ggl.credentials import get_credentials

log_dir = "/var/log/samba_sync"
working_dir = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir,'sync.log'),level=logging.WARNING)

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
parsed = LDIFParser(sys.stdin).parse()
datas = parsed.next()
data_dict = datas[1]

account_name = data_dict.get("sAMAccountName", False)
if (account_name):
    account_name = account_name[0]
    primaryEmail = account_name + "@" + DOMAIN
    # if no givenName, we use account_name
    givenName = data_dict.get('givenName', account_name)
    # if no familyName, we use account_name
    familyName = data_dict.get('sn', account_name)

passwd = data_dict.get("virtualCryptSHA512", False)
if (passwd):
    passwd = passwd[0]
    match = re.match("^\{CRYPT\}(.*)$", passwd)
    passwd = match.group(1)

deleted = data_dict.get("isDeleted", False)
if deleted:
    deleted = data_dict.get("isDeleted")[0] == 'TRUE'

logging.info("ACCOUNT : {}".format(account_name))
logging.info("PASSWORD : {}".format(passwd))
logging.info("DELETED : {}".format(deleted))

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
