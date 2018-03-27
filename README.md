# samba_gsync
Simple one way password synchronization from samba 4 (>=4.7) to G Suite
# installation & run
I've made tested this on a fresh debian 9 install, with Samba 4.8.0 built from sources, and configured
following https://wiki.samba.org/index.php/Setting_up_Samba_as_an_Active_Directory_Domain_Controller

1. Go to /usr/local/ and clone this repo, cd to the repo
2. Go to your G Suite console, start or use an existing project, create credentials and get the OAuth 2.0 'client_secret.json' file
3. Put this file in current dir
4. Get API client :
```bash
pip install --upgrade google-api-python-client
```
5. First, launch `./initialize_credentials.py`
6. Get sure samba is up and running, and you should be able to `./start_syncing.sh` and `./stop_syncing`
7. The sync.py script should not be called directly (meant to be called by samba directly)
