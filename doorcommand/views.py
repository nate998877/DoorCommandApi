from doorcommand.doorscripts.WildApricot import get_user
from random import randrange
from doorcommand.serializers import *
from doorcommand.models import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import views, viewsets
import subprocess
import os
from base64 import b64encode
import requests
from dotenv import load_dotenv
load_dotenv()


class TokenAuthSupportQueryString(TokenAuthentication):
    """
    Extend the TokenAuthentication class to support querystring authentication
    in the form of "http://www.example.com/?token=<token_key>"
    The wild apricot webhook doesn't have the option to send tokens in the body
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

    levels = {
        '725879': 'full-member-auto-pay',
        '969396': 'full-member-invoiced',
        '725880': 'general-member-auto-pay',
        '969397': 'general-member-invoiced',
        '1028621': 'student-membership',
        '1064884': 'student-membership-plus',
        '725412': 'guest-member'
    }

    # Devs updated the docs for webhook status codes. I believe them to be incorrect more testing needed
    # Dev codes [1 = Active, 2 = Lapsed, 3 = PendingRenewal, 20 = PendingNew, 30 = PendingUpgrade]
    status = {
        '0': "active",
        '1': "lapsed",
        '20': "pending-new",
        '30': "pending-renewal",
        '40': "pending-level-change",
        '50': "suspended",
    }
    # emulate bijective map functionality
    levels.update(dict(map(reversed, levels.items())))
    status.update(dict(map(reversed, status.items())))

    def post(self, request):
        parsed = request.data['Parameters']
        if ('Membership.Status' not in parsed):
            # If status isn't contained we don't care about the request.
            return Response(status=312)


        user_id = parsed["Contact.Id"]
        membership_level = parsed["Membership.LevelId"]
        membership_status = parsed["Membership.Status"]
        
        if(membership_level == levels['guest-member']):
            user = self.queryset.get(user_id=user_id)
            if(user):
                user.delete()
            return Response(status=400)

        if(membership_status == status['pending-new']):
            user = NewUserSerializer(data={
                "user_id": user_id,
                "status": status["20"],
                "level": membership_level
            })

            if not user.is_valid():
                return Response(status=500)

            user.save()
            return Response(status=200)

        elif(membership_status == status["active"]):
            user = self.queryset.get(user_id=user_id)

            if(not user):
                fetched_user = get_user(user_id)
                membership_level = fetched_user['MembershipLevel']['Id']
                if(membership_level != levels['guest-member']):
                    user = NewUserSerializer(data={
                        "user_id": user_id,
                        "status": status["20"],
                        "level": membership_level
                    })
                    if not user.is_valid():
                        return Response(status=500)
            else:
                user.status = 'active'
            user.save()

            #TODO: subscribe to door
            self.webhook(user_id, True)
            return Response(status=200)

        elif(membership_status == status["lapsed"] or membership_status == status["suspended"]):
            user = self.queryset.get(user_id=user_id)
            user.status = 'terminated'
            user.save()
            #TODO: remove from door

        return Response(status=412)

    def webhook(self, contact_id, old=False):
        apikey = os.getenv('API_KEY')
        headers = {
            'Authorization': f'Basic {b64encode(bytes(f"APIKEY:{apikey}", "utf-8")).decode("utf-8")}',
            'Content-type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'client_credentials',
            'scope': 'auto'
        }

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

        # I've done it this way to prevent removing a member from a group. I can't find information on what is and isn't necessary in this regard.

        # Get current values of group participation
        group_field = list(filter(
            lambda x: x['FieldName'] == 'Group participation', member['FieldValues']))

        # append new value to existing values
        group_field[0]['Value'].append({
            "Id": 559646,
            "Label": "tmpCardGroup"
        })
        member['FieldValues'] = group_field

        r = requests.put(
            f'https://api.wildapricot.org/v2.2/accounts/{account_id}/contacts/{contact_id}', headers=headers, json=member)

    def get(self, request):
        q = self.queryset.all()
        serializer = NewUserSerializer(q, many=True)
        return Response(serializer.data)


class RandPassView(views.APIView):
    queryset = NewUser.objects.all()
    serializer_class = TmpPassSerializer

    def get(self, request, *args, **kwargs):
        random_num = randrange(1000, 9999)
        user = None
        if request.data:
            user = self.queryset.get(user_id=request.data['userId'])
        if user.status == 'active':
            user.tmp_pass = random_num
            subprocess.call(
                ['python', 'doorcommand/doorscripts/subscribePassToDoor.py', random_num])
            user.save()
            return Response({"success": True, "randpass": random_num})
