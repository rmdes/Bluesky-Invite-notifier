#!/usr/bin/python3

import os
import json
import http.client, urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
NTFY_SH_SERVER = os.getenv("NTFY_SH_SERVER")

print("Starting the script.")

# Reading accounts.json
print("Reading accounts from accounts.json.")
with open('accounts.json', "r") as inputfile:
    accounts = json.load(inputfile)
print(f"Loaded {len(accounts)} accounts.")

# Establishing HTTPS connection
print("Establishing HTTPS connection to bsky.social.")
connection = http.client.HTTPSConnection("bsky.social")

def bskyget(url, data, headers = {}):
    print(f"Sending GET request to {url}.")
    params = urllib.parse.urlencode(data)
    connection.request("GET", url+'?'+params, '', headers)
    response = connection.getresponse()
    return response.read().decode()

def bskypost(url, data):
    print(f"Sending POST request to {url}.")
    params = json.dumps(data)
    headers = {"Content-type": "application/json"}
    connection.request("POST", url, params, headers)
    response = connection.getresponse()
    return response.read().decode()

didlist = {}

class BlueskyAccount:
    def __init__(self, handle):
        print(f"Initializing BlueskyAccount for {handle}.")
        self.handle = handle
        self.password = accounts[handle]
        self.getDid()
        self.getToken()

    def getDid(self):
        print(f"Getting DID for {self.handle}.")
        data = json.loads(bskyget('/xrpc/com.atproto.identity.resolveHandle', {'handle': self.handle}))
        if "error" in data:
            raise Exception({"handle": self.handle, "getDid": data})
        self.did = data['did']
        didlist[self.did] = self.handle

    def getToken(self):
        print(f"Getting Token for {self.handle}.")
        data = json.loads(bskypost('/xrpc/com.atproto.server.createSession', {'identifier': self.did, 'password': self.password}))
        if "error" in data:
            raise Exception({"handle": self.handle, "getToken": data})
        self.token = data['accessJwt']

    def getInvites(self):
        print(f"Getting invites for {self.handle}.")
        data = json.loads(bskyget('/xrpc/com.atproto.server.getAccountInviteCodes', {}, {'Authorization': 'Bearer '+self.token}))
        return data['codes']

# Collecting invite codes
print("Collecting invite codes.")
inviteCodes = {}
for handle in accounts:
    try:
        print(f"Processing account: {handle}")
        account = BlueskyAccount(handle)
        for code in account.getInvites():
            inviteCodes[code['code']] = code
    except Exception as err:
        print(f"Unexpected error: {err}, {type(err)}")

connection.close()

# Initialize counters
total_invite_codes = 0
used_invite_codes = 0

# Count the total number of invite codes and the number of used invite codes
for code, details in inviteCodes.items():
    total_invite_codes += 1
    if len(details['uses']) > 0:
        used_invite_codes += 1

print(f"Total invite codes: {total_invite_codes}")
print(f"Used invite codes: {used_invite_codes}")


# Print all invite codes
#print("All Invite Codes:")
#for code, details in inviteCodes.items():
#    account = didlist.get(details['forAccount'], 'Unknown Account')
#    created_at = details['createdAt']
#    uses = details['uses']
#
#    # Check if the code is used or not
#    if len(uses) > 0:
#        status = 'Used'
#        used_by = ', '.join([use['usedBy'] for use in uses])
#        used_at = ', '.join([use['usedAt'] for use in uses])
#    else:
#        status = 'Unused'
#        used_by = 'N/A'
#        used_at = 'N/A'
#
#    print(f"Code: {code}")
#    print(f"  Account: {account}")
#    print(f"  Created At: {created_at}")
#    print(f"  Status: {status}")
#    print(f"  Used By: {used_by}")
#    print(f"  Used At: {used_at}")
#    print("------")


# Reading old invite codes
print("Reading old invite codes from inviteCodes.json.")
if os.path.isfile('inviteCodes.json'):
    with open('inviteCodes.json', "r") as inputfile:
        inviteCodesBefore = json.load(inputfile)
else: 
    inviteCodesBefore = {}

# Comparing old and new invite codes
print("Comparing old and new invite codes.")
codes = {}
newcodes = {}
oldcodes = {}

for code in inviteCodesBefore:
    codes[code] = 1

for code in inviteCodes:
    if len(inviteCodes[code]['uses']) == 0:
        if not code in codes:
            newcodes[code] = 1
        else:
            oldcodes[code] = 1
    codes[code] = 1

if len(newcodes) > 0:
    print('NEW CODES FOUND:')
    for code in newcodes:
        print(code, didlist[inviteCodes[code]['forAccount']])

if len(oldcodes) > 0:
    print('Un-used old codes:')
    for code in oldcodes:
        print(code, didlist[inviteCodes[code]['forAccount']])

if len(newcodes) > 0:
    # Send the codes to the webhook
    print("Sending new codes to the webhook.")
    connection = http.client.HTTPSConnection(NTFY_SH_SERVER)

    def webhookpost(url, data):
        params = json.dumps(data)
        headers = {"Content-type": "application/json"}
        connection.request("POST", url, params, headers)
        response = connection.getresponse()
        return response.read().decode()
    
    for code in newcodes:
        try:
            response = webhookpost(WEBHOOK_URL, {'code': code, 'account': didlist[inviteCodes[code]['forAccount']], 'createdAt': inviteCodes[code]['createdAt']})
            print(f"HTTP Response: {response}")
        except Exception as e:
            print(f"Error occurred while sending POST request: {e}, {type(e)}")


    connection.close()

# Saving the new list of invite codes
print("Saving the new list of invite codes to inviteCodes.json.")
with open('inviteCodes.json', "w") as outfile:
    json.dump(inviteCodes, outfile)

print("Script execution complete.")
