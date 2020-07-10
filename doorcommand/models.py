from django.db import models

class NewUser(models.Model):
    user_id = models.CharField(max_length=128)
    tmp_pass = models.IntegerField(blank=True, null=True)
    STATUES = [('pending', 'pending'), ('active', 'active'), ('awaiting_card', 'awaiting_card')]
    status = models.CharField(max_length=128,  choices=STATUES)