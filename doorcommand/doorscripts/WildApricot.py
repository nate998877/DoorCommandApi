import requests
from base64 import b64encode
import json


def Method_A(contact_id):
    apikey = 'gfok08m5jfmwlr2zmw72l2bv04y566'
    headers = {
        'Authorization': 'Basic ' + b64encode(bytes('APIKEY:' + apikey, 'utf-8')).decode("utf-8"),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'grant_type': 'client_credentials',
        'scope': 'auto'
    }
    #Get Bearer token
    r = requests.post('https://oauth.wildapricot.org/auth/token',
                    headers=headers, data=payload)
    account = r.json()
    account_id = account['Permissions'][0]['AccountId']
    token = account['access_token']
    
    
    headers = {'User-Agent': 'doorCommand/0.1',
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'}

    r = requests.get(
        f'https://api.wildapricot.org/v2.2/accounts/{account_id}/contacts/{contact_id}', headers=headers)
    member = r.json()
    
    
    #I've done it this way to prevent removing a member from a group. I can't find information on what is and isn't necessary in this regard.
    
    #Get current values of group participation
    group_field = list(filter(
        lambda x: x['FieldName'] == 'Group participation', member['FieldValues']))

    #append new value to existing values
    group_field[0]['Value'].append(
        {"Id": 559646,
        "Label":"tmpCardGroup"}
        )
    
    #remove all other fields from user model & update group participation.
    member['FieldValues'] = group_field

    #This always returns 200 even if no update occurs, The api key used is read only, or even if incorrectly formatted data is sent. Security through obscurity?
    r = requests.put(
        f'https://api.wildapricot.org/v2.2/accounts/{account_id}/contacts/{contact_id}', headers=headers, json=member)

    # This just shows that the model isn't updated. you can copy the above request
    # & change requests.put to requests.get and remove json=member to do a follow up get to see that it hasn't updated
    print(json.dumps(r.json(), indent=2))
    print(r.status_code)


Method_A(43908758)