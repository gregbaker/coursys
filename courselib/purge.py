import datetime
from dataclasses import dataclass
from typing import Iterable, List, Type, TypeVar
from django.apps import apps
from django.db import models, transaction
from django.utils import timezone
from courselib import graphlib  # can be simply "import graphlib" in Python >= 3.9


T = TypeVar('T')
def flatten(xss: Iterable[Iterable[T]]) -> Iterable[T]:  # from https://stackoverflow.com/a/952952
    return (x for xs in xss for x in xs)


def toposort(model_classes: Iterable[Type[models.Model]]) -> Iterable[Type[models.Model]]:
    """
    Sort the model classes so foreign-key-related things are removed in the a legal order.
    """
    graph = {
        cls: {m.model for m in PurgeIfNoForeignKeyReferences.all_foreign_keys_to(cls) if m.model != cls}
        for cls in model_classes
    }
    ts = graphlib.TopologicalSorter(graph)
    return ts.static_order()
    

def purge_all(verbosity: int = 0, commit: bool = False) -> None:
    """
    For each model class with a .purge_policy, actually do the purging.
    """
    model_classes = flatten(i.get_models() for i in apps.get_app_configs())
    model_classes = toposort(model_classes)
    purgeable = [c for c in model_classes if hasattr(c, 'purge_policy')]

    for cls in purgeable:
        policy = getattr(cls, 'purge_policy')
        assert(isinstance(policy, PurgePolicy))
        policy.purge_purgable(cls, verbosity=verbosity, commit=commit)


class PurgePolicy:
    """
    Abstract base class for data purge policies.
    """
    # subclasses must implement exactly one of these methods:
    def purgeable_queryset(self, model_class: Type[models.Model]) -> models.QuerySet[models.Model]:
        raise NotImplementedError()
    def purgeable_instances(self, model_class: Type[models.Model]) -> Iterable[models.Model]:
        raise NotImplementedError()
    
    def all_filefields(self, model_class: Type[models.Model]) -> list[models.FileField]:
        return [f for f in model_class._meta.get_fields() if isinstance(f, models.FileField)]
    
    def purge_purgable(self, model_class: Type[models.Model], verbosity: int = 1, commit: bool = False) -> None:
        filefields = self.all_filefields(model_class)

        try:
            to_delete = self.purgeable_queryset(model_class)

        except NotImplementedError:
            to_delete = list(self.purgeable_instances(model_class))
            if verbosity > 0:
                print(f'Purging {len(to_delete)} instances of {model_class.__name__}')
        
        else:
            if verbosity > 0:
                print(f'Purging {to_delete.count()} instances of {model_class.__name__}')
            if not filefields:
                # the easy case: can just .delete the whole queryset and be done with it.
                if verbosity > 1:
                    print(f"   deleting {to_delete}")

                if commit:
                    to_delete.delete()
                
                return

        if verbosity == 2:
            print(f"  deleting {to_delete}")

        # handle either/both: it's a list that we have to iterate through; there are FileFields that need their files deleted
        for i in to_delete:
            if verbosity > 2:
                print(f"  deleting {i}")
            if commit:
                with transaction.atomic():
                    # If this fails mid-transaction, it would probably leave the instance in an inconsistent state:
                    # referencing files that are no longer there. On the bright side, we can fix it by deleting the
                    # row, since it's scheduled to be purged anyway.
                    for ff in filefields:
                        fieldfile = getattr(i, ff.name)
                        if fieldfile is not None:
                            fieldfile.delete(save=False)
                    i.delete()


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

@dataclass
class AnyHiddenPurgePolicy(PurgePolicy):
    """
    Policy that will purge items if they (or foreign-key-related objects) have .hidden==True
    """
    hidden_fields: List[str]
    
    def purgeable_queryset(self, model_class):
        # do *any* of the listed .hidden fields have a True?
        qs = model_class.objects.none()
        for f in self.hidden_fields:
            qs = qs | model_class.objects.filter(**{f: True})
        return qs


class PurgeIfNoForeignKeyReferences(PurgePolicy):
    """
    Policy for data that can be deleted if no other data references it via ForeignKey or ManyToManyField.

    Possible enhancement: keep config field to mark when it was identifies as having no references, and only purge a fixed time after that;
    or accept some kind of additional filter in the constructor?
    """
    @staticmethod
    def all_foreign_keys_to(model_class: Type[models.Model]) -> Iterable[models.ForeignKey | models.ManyToManyField]:
        """
        Return all ForeignKey and ManyToManyField fields in the project that point to model_class.
        """
        app_models = apps.get_models()
        fk_fields = flatten(
            (
                field for field in m._meta.get_fields()
                if isinstance(field, (models.ForeignKey, models.ManyToManyField))
                and field.related_model == model_class
            )
            for m in app_models
        )
        return fk_fields

    @staticmethod
    def all_instances_referenced(model_class: Type[models.Model]) -> set[models.Model]:
        """
        Return all instances of model_class that are referenced by any other model via ForeignKey or GenericForeignKey.
        """
        fk_fields = PurgeIfNoForeignKeyReferences.all_foreign_keys_to(model_class)
        referenced = (
            set(field.model.objects.filter(
                **{f'{field.name}__isnull': False}
            ).values_list(field.name, flat=True))
            for field in fk_fields
        )
        return set(flatten(referenced))

    def purgeable_queryset(self, model_class):
        # TODO: reactivate purgeable_queryset_real when convinced it's fully safe
        return model_class.objects.none()

    def purgeable_queryset_real(self, model_class):
        refs = PurgeIfNoForeignKeyReferences.all_instances_referenced(model_class)
        unreferenced = model_class.objects.exclude(pk__in=refs)
        return unreferenced
