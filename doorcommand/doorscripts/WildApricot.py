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
        token = account['access_token']
        self.headers = {'User-Agent': 'doorCommand/0.1',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'}
    
    
    def get_user(self, contact_id):
        r = requests.get(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts/{contact_id}', headers=self.headers)
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

        #!This returns 200 even if no update occurs due to errors/incorrect formating or key, cannot be use to validate succesful change :/
        r = requests.put(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts/{contact_id}', headers=self.headers, json=member)
    
    
    def initalize_db(self):
        # ?$async=false&OTHER_QUERY_PARAMS
        #? Add a query to only get active memebers?
        params = {
            '$async': 'false',
            '$filter': "'Access Card ID' ne NULL AND 'Membership level ID' ne 725412 AND 'Membership status' ne 'Lapsed'"
        }
        r = requests.get(f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts', headers=self.headers, params=params)
        
        #todo: "FieldName": "Access Code", "FieldName": "Access Card ID"
        
        # this can be something like loop for 1st one get custom code, get index of items. For all subsequent members 
        # check systemcode vs saved code if match use index
        for x in r.json()['Contacts']:
            for y in x['FieldValues']:
                if y["FieldName"] == "Access Code":
                    foo = y["Value"]
                if y["FieldName"] == "Access Card ID":
                    foo2 = y["Value"]
            print(x["FirstName"], x["LastName"], x["MembershipLevel"]["Name"], foo, foo2)
            print(len(r.json()['Contacts']))
        # print(json.dumps(x, indent=2))
        
    def get_cards(self):
        params = {
            '$async': 'false',
            '$filter': "'Access Card ID' ne NULL AND 'Membership level ID' ne 725412 AND 'Membership status' ne 'Lapsed'"
        }
        r = requests.get(f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts', headers=self.headers, params=params)
        card_list = list()
        for x in r.json()['Contacts']:
            for y in x['FieldValues']:
                if y["FieldName"] == "Access Card ID":
                    card_list.append(y['Value'])
        return card_list
        

# a = Apricot()

# print(a.get_cards())