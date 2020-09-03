from doorcommand.doorscripts.subscribePassToDoor import Door_Controller
from doorcommand.doorscripts.WildApricot import Apricot
from random import randrange
from doorcommand.serializers import *
from doorcommand.models import *
# from rest_framework.decorators import action
import rest_framework
from rest_framework.response import Response
from rest_framework import views, viewsets
import subprocess
import os
from base64 import b64encode
import requests
from dotenv import load_dotenv
load_dotenv()


class TokenAuthSupportQueryString(rest_framework.authentication.TokenAuthentication):
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
    permission_classes = [rest_framework.permissions.IsAuthenticated]
    
    apricot = Apricot()


    def post(self, request):
        parsed = request.data['Parameters']
        if ('Membership.Status' not in parsed):
            # If status isn't contained we don't care about the request.
            return Response(status=312)

        print(parsed)

        user_id = int(parsed["Contact.Id"])
        membership_level = int(parsed["Membership.LevelId"])
        membership_status = int(parsed["Membership.Status"])

        # if(membership_level == NewUser.GUESTMEMBER):
        #     return Response(status=401)
            
        #TODO: delete this For debugging ^ re-enable once done
        if(membership_level == NewUser.GUESTMEMBER):
            user = NewUserSerializer(data={
                "user_id": user_id,
                "status": NewUser.PENDINGNEW,
                "level": membership_level
            })

            if not user.is_valid():
                return Response(status=500)

            user.save()
            return Response(status=200)
        
        
        
        
            
        
        
        user = User.objects.get(user_id=user_id)
        if(user):
            #TODO: handle handle users looking to reset pass this will probably be passed to a different function
            return Response(200)


        if(membership_status == NewUser.PENDINGNEW):
            user = NewUserSerializer(data={
                "user_id": user_id,
                "status": NewUser.PENDINGNEW,
                "level": membership_level
            })
            
            #TODO: Log this
            if not user.is_valid():
                return Response(status=500)

            user.save()
            return Response(status=200)

        elif(membership_status == NewUser.ACTIVE):
            user = self.queryset.get(user_id=user_id)

            if(not user):
                #TODO: Log this. Chances are program wasn't running when user signed up :(
                fetched_user = self.apricot.get_user(user_id)
                membership_level = int(fetched_user['MembershipLevel']['Id'])
                if(membership_level != NewUser.GUESTMEMBER):
                    user = NewUserSerializer(data={
                        "user_id": user_id,
                        "status": NewUser.ACTIVE,
                        "level": membership_level
                    })
                    if not user.is_valid():
                        return Response(status=500)
            else:
                user.status = 'active'
            user.save()
            
            self.apricot.add_user_to_cardgroup(user_id)

            return Response(status=200)

        #if user isn't new, isn't active, isn't already added to db then what are they?
        #TODO: Log this
        return Response(status=412)

    def get(self, request):
        """view saved users

        Args:
            request (dict): request information

        Returns:
            Response: Seralized user data
        """
        q = self.queryset.all()
        serializer = NewUserSerializer(q, many=True)
        return Response(serializer.data)


class RandPassView(views.APIView):
    """
    Generate a random password for 1-time use when setting up a new rfid card
    """
    queryset = NewUser.objects.all()
    serializer_class = TmpPassSerializer

    def get(self, request, *args, **kwargs):
        random_num = randrange(1000, 9999)
        user = None
        try:
            if request.data:
                user = self.queryset.get(user_id=request.data['userId'])
            if user.status == 'active':
                user.tmp_pass = random_num
                #TODO: change this to just call the script it doesn't need to be a subprocess
                subprocess.call(
                    ['python', 'doorcommand/doorscripts/subscribePassToDoor.py', random_num])
                
                user.save()
                return Response({"success": True, "randpass": random_num})
                
        except:
            #TODO: add comprehensive response for no user found/incorrect data
            return Response(status=404)
