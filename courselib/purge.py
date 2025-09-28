import datetime
from dataclasses import dataclass
from typing import Iterable, Type
from django.db import models
from django.utils import timezone


def flatten(xss):  # from https://stackoverflow.com/a/952952
    return (x for xs in xss for x in xs)


class PurgePolicy:
    """
    Abstract base class for data purge policies.
    """
    # subclasses must implement exactly one of these methods:
    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        raise NotImplementedError()
    def purgeable_instances(self, model_class: Type[models.Model]) -> Iterable[models.Model]:
        raise NotImplementedError()


@dataclass
class AgePurgePolicy(PurgePolicy):
    """
    Policy for data that can simply be deleted after a certain time, based on some date or datetime field.
    """
    age_field: str
    after_days: int

    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        cutoff = timezone.now() - datetime.timedelta(days=self.after_days)
        filter_kwargs = {f'{self.age_field}__lt': cutoff}
        return model_class.objects.filter(**filter_kwargs)


class ThisIsPublicData(PurgePolicy):
    """
    Policy for data that is fully public and has no privacy or retention concerns.
    """
    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        return model_class.objects.none()


class PurgeIfNoForeignKeyReferences(PurgePolicy):
    """
    Policy for data that can be deleted if no other data references it via ForeignKey or ManyToManyField.

    Possible enhancement: keep config field to mark when it was identifies as having no references, and only purge a fixed time after that;
    or accept some kind of additional filter in the constructor?
    """
    @staticmethod
    def all_foreign_keys_to(model_class: Type[models.Model]) -> Iterable[models.ForeignObjectRel]:
        """
        Return a dict mapping model classes to lists of model classes that have ForeignKey references to them.
        """
        return (field for field in model_class._meta.get_fields() if isinstance(field, models.ForeignObjectRel))

    @staticmethod
    def all_instances_referenced(model_class: Type[models.Model]) -> set[models.Model]:
        """
        Return all instances of model_class that are referenced by any other model via ForeignKey or GenericForeignKey.
        """
        fk_fields = PurgeIfNoForeignKeyReferences.all_foreign_keys_to(model_class)
        referenced = (
            set(field.related_model.objects.filter(
                **{f'{field.field.name}__isnull': False}
            ).values_list(field.field.name, flat=True))
            for field in fk_fields
        )
        return set(flatten(referenced))

    def purgeable_queryset(self, model_class):
        refs = PurgeIfNoForeignKeyReferences.all_instances_referenced(model_class)
        unreferenced = model_class.objects.exclude(pk__in=refs)
        return unreferenced
