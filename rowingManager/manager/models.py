from django.db import models
from django.contrib.auth.models import User
from annoying.fields import AutoOneToOneField


class Erg(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ErgBooking(models.Model):
    erg = models.ForeignKey(Erg, on_delete=models.CASCADE)
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    startTime = models.TimeField()
    hours = models.IntegerField()


class RowerProfile(models.Model):
    user = AutoOneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    crsid = models.CharField(max_length=8)


class Boat(models.Model):
    name = models.CharField(max_length=255)
    scull = models.BooleanField()
    size = models.IntegerField()
    coxed = models.BooleanField()

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Outing(models.Model):
    STATUS_TYPES = [('P', 'Pending'), ('CF', 'confirmed'), ('CC', 'cancelled')]
    date = models.DateField()
    boat = models.ForeignKey(Boat, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    meetingTime = models.TimeField()
    status = models.CharField(max_length=2, choices=STATUS_TYPES)


class InTeam(models.Model):
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    constraints = [
        models.UniqueConstraint(fields=['person', 'team'], name='unique combination')
    ]

    def __str__(self):
        return self.person.username + " : " + self.team.name


class InOuting(models.Model):
    OUTING_ROLES = [('RW', 'rower'), ('CX', 'cox'), ('CC', 'coach')]
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    outing = models.ForeignKey(Outing, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=OUTING_ROLES)


class Available(models.Model):
    OUTING_ROLES = [('RW', 'rower'), ('CX', 'cox'), ('CC', 'coach')]
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    outing = models.ForeignKey(Outing, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=OUTING_ROLES)


class ErgWorkout(models.Model):
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    distance = models.IntegerField()
    minutes = models.IntegerField()
    seconds = models.IntegerField()
    subSeconds = models.IntegerField()
