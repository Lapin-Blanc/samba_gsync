# samba_gsync
Simple one way password synchronization from samba 4 (>=4.7) to G Suite

# installation & run
I've tested this with a fresh Centos 7 Samba 4.8.2 built from sources and configured
as explained described there :

1. Go to /usr/local/ and clone this repo, cd to the repo
2. Edit the config.json file with :
```python
{
    "domain" : "yourdomain.com",
    "protected_accounts" : [ "administrator", "super.user"]
}
```
3. Go to your G Suite console, start or use an existing project, create credentials and get the OAuth 2.0 
'client_secret_XXX.json' file and rename it to 'client_secret.json',
4. Put this file in the 'ggl' dir and chmod it to 600
5. Get Google API client and ldif3:
```bash
pip install --upgrade google-api-python-client
pip install ldif3
```
6. First, launch `./initialize_credentials.py`
7. Add `password hash userPassword schemes = CryptSHA512` to smb.conf
8. Get sure samba is up and running, and you should be able to `./start_syncing.sh` and `./stop_syncing`
9. You can check logs at  /var/log/samba_sync/sync.log and /var/log/samba_sync/user-syncpasswords.log
10. Once everything is fine, you can copy, start and enable the startup script :
    - cp samba-gsync.service /etc/systemd/system/
    - chmod +x /etc/systemd/system/samba-gsync.service
    - systemctl start samba-gsync.service
    - systemctl enable samba-gsync.service
11. The sync.py script should not be called directly (meant to be called by samba directly)

## Behaviour
Whenever you create a local domain user account, either from RSAT or from samba-tool, 
this account is also created on the G Suite domain. Synced attributes are primaryEmail, 
givenName and familyName and G Suite email is build with _username@domain.com_


If you don't provide a givenName and/or familyName, username will be used instead.

If you modify the password, it gets updated (that's the whole point...).

If you delete a local user account **it is also deleted** on the G Suite domain.

Accounts mentionned in the config file are protected though.
