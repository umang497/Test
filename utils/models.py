import uuid

from django.db import models


class BaseModel(models.Model):

    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class BaseUUIDModel(BaseModel):

    class Meta:
        abstract = True

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)


class RecurrenceFrequency(models.IntegerChoices):
    WEEKLY = (7, "Weekly")
