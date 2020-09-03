from django.db import models
from django.utils.translation import gettext_lazy as _


class NewUser(models.Model):
    # According to devs : Membership.Status
    # [1 = Active, 2 = Lapsed, 3 = PendingRenewal, 20 = PendingNew, 30 = PendingUpgrade]

    # TODO: Test these statuses and confirm that developer statuses are accurate!
    ACTIVE = '1'
    LAPSED = '2'
    PENDINGRENEWAL = '3'
    PENDINGNEW = '20'
    PENDINGUPGRADE = '30'
    AWAITINGCARD = '100'

    FULLMEMBERAUTOPAY = 725879
    FULLMEMBERINVOICED = 969396
    GENERALMEMBERAUTOPAY = 725880
    GENERALMEMBERINVOICED = 969397
    STUDENTMEMBERSHIP = 1028621
    STUDENTMEMBERSHIPPLUS = 1064884
    GUESTMEMBER = 725412

    STATUS = [
        (ACTIVE, 'active'),
        (LAPSED, 'lapsed'),
        (PENDINGRENEWAL, 'pending'),
        (PENDINGNEW, 'pending'),
        (PENDINGUPGRADE, 'pending'),
        (AWAITINGCARD, 'awaiting_card'),
    ]

    LEVEL = [
        (FULLMEMBERAUTOPAY, 'full_member'),
        (FULLMEMBERINVOICED, 'full_member'),
        (GENERALMEMBERAUTOPAY, 'general_member'),
        (GENERALMEMBERINVOICED, 'general_member'),
        (STUDENTMEMBERSHIP, 'student_member'),
        (STUDENTMEMBERSHIPPLUS, 'student_member'),
        (GUESTMEMBER, 'guest_member'),
    ]

    user_id = models.IntegerField()
    tmp_pass = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(choices=STATUS)
    level = models.IntegerField(choices=LEVEL)


class User(models.Model):
    FULL = 1
    PARTIAL = 2
    ADMIN = 0

    LEVEL = [
        (FULL, 'full'),
        (PARTIAL, 'partial'),
        (ADMIN, 'admin')
    ]

    user_id = models.IntegerField()
    card_id = models.IntegerField()
    password = models.IntegerField()
    level = models.IntegerField(choices=LEVEL)
