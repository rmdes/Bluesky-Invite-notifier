# Bluesky-Invite-notifier
Get a ntfy.sh notification when you get a Bluesky Invite

## Dependency
pip install python-dotenv

## How to use
- cp env.smaple .env
- cp accounts.json-sample accounts.json
- fill your handle and app passowrd
- create a ntfy.sh topic (the script does not handle auth to ntfy.sh, so pick a random name for the topic, think of it as a password)
- adapt .env with your topic and ntfy.sh server
- Install ntfy.sh mobile app and subscribe to the topic to get notifications on your phone
- `python3 scanBlueInvites.py`

## Optional : run a cron job every hours & almost forget :)
- chmod +x scanBlueInvites.py
- crontab -e
- copy this line and adapt to your script path

`0 * * * * cd /home/scripts/invites-notifier && /usr/bin/python3 scanBlueInvites.py >> cron.log 2>&1
`
## Credit

[mwyann.fr](https://github.com/Mwyann/)
