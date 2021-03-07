from rest_framework.response import Response
from doorcommand.serializers import (
    NewUserSerializer,
    # UserSerializer,
    # TmpPassSerializer
)


def save_user(user_id, NewUser, membership_level):
    user = NewUserSerializer(data={
        "user_id": user_id,
        "status": NewUser.PENDINGNEW,
        "level": membership_level
    })

    if not user.is_valid():
        return Response(status=500)

        user.save()
        return user
