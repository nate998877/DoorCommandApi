import os
import rest_framework
from doorcommand.serializers import (
    NewUserSerializer,
    # UserSerializer,
    TmpPassSerializer
)
from doorcommand.doorscripts.subscribePassToDoor import Door_Controller
from doorcommand.doorscripts.WildApricot import Apricot
from doorcommand.models import NewUser, User
from random import randrange
# from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import views
import logging

from threading import Thread

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


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

        user_id = int(parsed["Contact.Id"])
        membership_level = int(parsed["Membership.LevelId"])
        membership_status = int(parsed["Membership.Status"])

        print(parsed)

        def save_user():
            user = NewUserSerializer(data={
                "user_id": user_id,
                "status": NewUser.PENDINGNEW,
                "level": membership_level
            })

            if not user.is_valid():
                return Response(status=500)

            user.save()
            return user

        # if(membership_level == NewUser.GUESTMEMBER):
        #     return Response(status=401)
        try:
            user = User.objects.get(user_id=user_id)
            if(user):
                #TODO: handle handle users looking to get new card/update pass
                return Response(200)
        except:
            pass

        if(int(membership_status) == int(NewUser.PENDINGNEW)):
            save_user()
            return Response(status=200)

        elif(int(membership_status) == int(NewUser.ACTIVE)):
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
                user.status = NewUser.ACTIVE
            user.save()

            self.apricot.add_user_to_cardgroup(user_id)

            return Response(status=200)

        #if user isn't new, isn't active, isn't already added to db, yet triggered the webhook then what are they?
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
    dc = Door_Controller('e63a')

    def post(self, request, *args, **kwargs):
        random_num = randrange(1000, 9999)
        user = None
        try:
            if request.data:
                user = self.queryset.get(user_id=request.data['userId'])
            if int(user.status) == int(NewUser.ACTIVE):
                user.tmp_pass = random_num

                #TODO: change this to just call the script it doesn't need to be a subprocess

                user.save()
                x = Thread(target=self.dc.upload_one_time_passwords, args=([os.getenv('ADMIN_ACCESS_CODE'), random_num],))
                x.start()
                data = {"success": True, "randpass": random_num}
                print(data)
                return Response(data)
        except:
            #TODO: add comprehensive response for no user found/incorrect data
            return Response(status=404)
        return Response(status=200)

    def options(self, requests, *args, **kwarsg):
        return Response(status=200)