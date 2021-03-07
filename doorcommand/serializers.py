from rest_framework.serializers import HyperlinkedModelSerializer
from doorcommand.models import NewUser

class NewUserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = NewUser
        fields = ['user_id', 'status', 'level']

class TmpPassSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = NewUser
        fields = ['tmp_pass']

class UserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = NewUser