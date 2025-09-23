import datetime
from typing import Iterable, Type
from django.db import models
from django.utils import timezone


class DataPurger:
    model_class: Type[models.Model]

    def age(self, days: int) -> datetime.datetime:
        return timezone.now() - datetime.timedelta(days=days)

    # Exactly one of these should be implemented in a subclass:

    def purge_queryset(self) -> models.QuerySet[models.Model]:
        raise NotImplementedError()
    
    def purge_instances(self) -> Iterable[models.Model]:
        raise NotImplementedError()