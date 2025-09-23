import datetime
from dataclasses import dataclass
from typing import Iterable, Type
from django.db import models
from django.utils import timezone


class PurgePolicy:
    # subclasses must implement exactly one of these methods:
    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        raise NotImplementedError()
    def purgeable_instances(self, model_class: Type[models.Model]) -> Iterable[models.Model]:
        raise NotImplementedError()


@dataclass
class AgePurgePolicy(PurgePolicy):
    age_field: str
    after_days: int

    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        cutoff = timezone.now() - datetime.timedelta(days=self.after_days)
        filter_kwargs = {f'{self.age_field}__lt': cutoff}
        return model_class.objects.filter(**filter_kwargs)
