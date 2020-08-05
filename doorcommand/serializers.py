from rest_framework.serializers import HyperlinkedModelSerializer
from doorcommand.models import *

class NewUserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = NewUser
        fields = ['user_id', 'status', 'level']

class TmpPassSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = NewUser
        fields = ['tmp_pass']
