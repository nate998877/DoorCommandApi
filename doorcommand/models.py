from django.db import models

class NewUser(models.Model):
    user_id = models.CharField(max_length=128)
    tmp_pass = models.IntegerField(blank=True, null=True)
    STATUS = [('pending', 'pending'), ('active', 'active'), ('awaiting_card', 'awaiting_card')]
    LEVEL = [('full-member', 'full-member'), ('general-member', 'general-member'), ('student-member', 'student-member'),('guest-member', 'guest-member')]
    status = models.CharField(max_length=128,  choices=STATUS)
    level = models.CharField(max_length=128,  choices=LEVEL)