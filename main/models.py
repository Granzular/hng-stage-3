from django.db import models
from uuid6 import uuid7


class Profile(models.Model):
    id = models.UUIDField( primary_key=True, default=uuid7, editable=False, db_index=True)
    name = models.CharField(max_length=100, unique=True,db_index=True)

    gender = models.CharField(max_length=10,db_index=True)
    gender_probability = models.FloatField()# 

    age = models.IntegerField()#
    age_group = models.CharField(max_length=10)#

    country_id = models.CharField(max_length=2,db_index=True)
    country_name = models.CharField(max_length=50)
    country_probability = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name 

    def save(self, *args, **kwargs):
        # normalize for case-insensitive uniqueness
        if self.name:
            self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['created_at']