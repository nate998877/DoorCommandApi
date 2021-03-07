import requests
import json
import os
from dotenv import load_dotenv
from base64 import b64encode

load_dotenv()


class Apricot():
    def __init__(self):
        apikey = os.getenv('API_KEY')
        headers = {
            'Authorization': f"Basic {b64encode(bytes(f'APIKEY:{apikey}', 'utf-8')).decode('utf-8')}",
            'Content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'client_credentials',
            'scope': 'auto'
        }

        # Get Bearer token
        r = requests.post(
            'https://oauth.wildapricot.org/auth/token',
            headers=headers,
            data=payload
        )
        account = r.json()

        token = account['access_token']
        self.account_id = account['Permissions'][0]['AccountId']
        self.headers = {
            'User-Agent': 'doorCommand/0.1',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def get_user(self, contact_id):
        """Get a single contact via contact_id

        Args:
            contact_id (int, str): contact id defined on wild apricot

        Returns:
            dict: api response object
        """
        r = requests.get(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts/{contact_id}',
            headers=self.headers
        )

        return r.json()

    def add_user_to_cardgroup(self, contact_id):
        member = self.get_user(contact_id)
        group_field = list(filter(
            lambda x: x['FieldName'] == 'Group participation', member['FieldValues']))

        # append append cardgroup to existing groups
        group_field[0]['Value'].append({
            "Id": 559646,
            "Label": "tmpCardGroup"
        })

        # remove all other fields from user model.
        member['FieldValues'] = group_field

        #! This returns 200 even if no update occurs due to errors/incorrect
        #! formatting or key, cannot be use to validate succesful change :/
        r = requests.put(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts/{contact_id}',
            headers=self.headers,
            json=member
        )

    def initalize_db(self):
        #? $async=false&OTHER_QUERY_PARAMS
        #? Add a query to only get active memebers?

        # async false is prefferable for small queries since you otherwise have to handle callback url
        params = {
            '$async': 'false',
            '$filter': "'Access Card ID' ne NULL AND 'Membership level ID' ne 725412 AND 'Membership status' ne 'Lapsed'" #has a card, isn't a guest, & is active
        }
        r = requests.get(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts',
            headers=self.headers,
            params=params
        )

        # TODO: This is to create a local database for when the network goes
        #  down to cross reference for updates missed durring downtime

        # I'm not sure if it's better to create a bunch of individual users and update one at a time or if it's possible to create one large
        # structure to add to the database?
        for contact in r.json()['Contacts']:
            for field in contact['FieldValues']:
                if field["FieldName"] == "Access Code":
                    access_code = field["Value"]
                if field["FieldName"] == "Access Card ID":
                    card_id = field["Value"]
            print(contact["FirstName"], contact["LastName"], contact["MembershipLevel"]["Name"], access_code, card_id)
        print(len(r.json()['Contacts']))

    def get_cards(self):
        params = {
            '$async': 'false',
            '$filter': "'Access Card ID' ne NULL AND 'Membership level ID' ne 725412 AND 'Membership status' ne 'Lapsed'"
        }
        r = requests.get(
            f'https://api.wildapricot.org/v2.2/accounts/{self.account_id}/contacts', headers=self.headers, params=params)
        card_list = list()
        for contact in r.json()['Contacts']:
            for field in contact['FieldValues']:
                if field["FieldName"] == "Access Card ID":
                    card_list.append(field['Value'])
        return card_list
