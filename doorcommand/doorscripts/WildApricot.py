import requests
from base64 import b64encode
import json
import os
from dotenv import load_dotenv
load_dotenv()


class Apricot():
    def __init__(self):
        apikey = os.getenv('API_KEY')
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
        self.account_id = account['Permissions'][0]['AccountId']
        self.token = account['access_token']
    
    
    def get_user(self, contact_id):
        headers = {'User-Agent': 'doorCommand/0.1',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'}
        r = requests.get(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts/{contact_id}', headers=headers)
        return r.json()
    
    
    def add_user_to_cardgroup(self, contact_id):
        member = self.get_user(contact_id)
        group_field = list(filter(
            lambda x: x['FieldName'] == 'Group participation', member['FieldValues']))

        #append append cardgroup to existing groups
        group_field[0]['Value'].append(
            {"Id": 559646,
            "Label":"tmpCardGroup"}
            )
    
        #remove all other fields from user model.
        member['FieldValues'] = group_field

        #This returns 200 even if no update occurs due to errors/incorrect formating or key, cannot be use to validate
        r = requests.put(
            f'https://api.wildapricot.org/v2.2/accounts/{account_id}/contacts/{contact_id}', headers=headers, json=member)

