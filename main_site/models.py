from django.db import models


class Result(models.Model):
    place = models.IntegerField()
    name = models.CharField(max_length=255)
    time = models.CharField(max_length=255)
