from dotenv import load_dotenv
load_dotenv()
import requests
from base64 import b64encode
import os
import subprocess
from rest_framework import views, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from doorcommand.models import *
from doorcommand.serializers import *
from random import randrange


class TokenAuthSupportQueryString(TokenAuthentication):
    """
    Extend the TokenAuthentication class to support querystring authentication
    in the form of "http://www.example.com/?token=<token_key>"
    """
    def authenticate(self, request):
        # Check if 'token_auth' is in the request query params.
        # Give precedence to 'Authorization' header.
        if 'token' in request.query_params and \
                        'HTTP_AUTHORIZATION' not in request.META:
            return self.authenticate_credentials(request.query_params.get('token'))
        else:
            return super(TokenAuthSupportQueryString, self).authenticate(request)




class NewUserView(views.APIView):
    queryset = NewUser.objects.all()
    serializer_class = NewUserSerializer
    authentication_classes = [TokenAuthSupportQueryString]
    permission_classes = [IsAuthenticated]

    
    def post(self, request):
        parsed = request.data['Parameters']
        if ('Membership.Status' not in parsed): 
            return Response(status=312)
        elif(parsed['Membership.Status'] == '20'):
            user = NewUserSerializer(data={
                "user_id": parsed["Contact.Id"],
                "status": "pending"
            })
            if user.is_valid():
                user.save()
                return Response(status=201)
        elif(parsed['Membership.Status'] == '0'):
            user = self.queryset.get(user_id=parsed["Contact.Id"])
            print(user)
            if user:
                self.webhook(parsed["Contact.Id"])
                
                
                user.status = 'active'
                user.save()
                return Response(status=200)

        return Response(status=412)
    
    def webhook(self, contact_id):
        apikey = os.getenv('API_KEY')
        headers = {
            'Authorization': 'Basic ' + b64encode(bytes('APIKEY:' + apikey, 'utf-8')).decode("utf-8"),
            'Content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type':'client_credentials',
            'scope':'auto'
        }
        
        r = requests.post('https://oauth.wildapricot.org/auth/token', headers=headers, data=payload)
        account_id = r.json()['Permissions'][0]['AccountId']
        
        headers = {'User-Agent': 'doorCommand/0.1',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + r.json()['access_token']}
                    
        r = requests.get('https://api.wildapricot.org/v2.2/accounts/'+str(account_id)+'/contacts/'+str(contact_id), headers=headers)
        user = r.json()
        group_field = list(filter(lambda x: x['FieldName'] == 'Group participation', user['FieldValues']))
        group_field[0]['Value'].append({
            "Id": 559646,
            "Label":'tmpCardGroup'
        })
        
        user['FieldValues'] = group_field
        
        r = requests.put('https://api.wildapricot.org/v2.2/accounts/'+account_id+'/contacts/'+contact_id, headers=headers, json={})



    def get(self, request):
        q = self.queryset.all()
        serializer = NewUserSerializer(q, many=True)
        return Response(serializer.data)




class RandPassView(views.APIView):
    queryset = NewUser.objects.all()
    serializer_class = TmpPassSerializer
    
    def get(self, request, *args, **kwargs):
        random_num = randrange(1000,9999)
        user = None
        print(request.data)
        if request.data:
            user = self.queryset.get(user_id=request.data['userId'])
        if user.status == 'active':
            user.tmp_pass = random_num
            subprocess.call(['python', 'doorcommand/doorscripts/subscribePassToDoor.py'])
            return Response({"success": True, "randpass":random_num})
