import itertools
import re
from typing import Type, Iterable

from django.conf import settings
from django.db import models

from django.core.management import call_command
from django.db.models import Q
from haystack import connections
from haystack.exceptions import NotHandled
from haystack.utils import loading
from haystack.utils.app_loading import haystack_get_models, haystack_load_apps

def find_userid_or_emplid(userid):
    """
    Search by userid or emplid
    """
    try:
        int(userid)
        return Q(userid=userid) | Q(emplid=userid)
    except ValueError:
        return Q(userid=userid)

def find_member(userid):
    """
    Search Member (or other thing with a .person) by userid or emplid
    """
    try:
        int(userid)
        return Q(person__userid=userid) | Q(person__emplid=userid)
    except ValueError:
        return Q(person__userid=userid)

# adapted from http://julienphalip.com/post/2825034077/adding-search-to-a-django-site-in-a-snap

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields, startonly=False):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    
    startonly=True searches only at start of field/word.
    '''
    query = Q() # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            if startonly:
                q = Q(**{"%s__istartswith" % field_name: term}) \
                    | Q(**{"%s__icontains" % field_name: ' '+term}) 
            else:
                q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


# aliases to the haystack tasks, for convenience

def haystack_update_index(update_only: bool = True):
    our_update_index(use_celery=False, update_only=update_only)


def haystack_rebuild_index():
    our_clear_index()
    our_update_index(use_celery=False, update_only=False)


def haystack_clear_index():
    our_clear_index()


# A function that can be called (possibly from a post_save handler or similar) to index specific instances
# without needing a full update/rebuild...
def haystack_index(model: Type[models.Model], qs: Iterable[models.Model], commit=True):
    """
    Create/update haystack index of collection of instances of the given `model`.

    i.e. imitate haystack's update_index.Command.handle, but only index `qs`, not some larger queryset

    e.g.
    haystack_index(Foo, Foo.objects.filter(interesting=True))
    """
    haystack_connections = loading.ConnectionHandler(settings.HAYSTACK_CONNECTIONS)
    backends = haystack_connections.connections_info.keys()
    for using in backends:
        backend = haystack_connections[using].get_backend()
        unified_index = haystack_connections[using].get_unified_index()
        index = unified_index.get_index(model)
        backend.update(index, qs, commit=commit)


# adapted from https://docs.python.org/2/library/itertools.html
# Used to chunk big lists into task-sized blocks.
def grouper(iterable, n):
    """
    Collect data into fixed-length chunks or blocks
    grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    groups = itertools.zip_longest(fillvalue=None, *args)
    return ((v for v in grp if v is not None) for grp in groups)


def our_update_index(group_size: int = 2500, update_only: bool = True, use_celery: bool = True):
    """
    Roughly equivalent to the Haystack update_index management command, but handles the work in reasonably-sized tasks.

    group_size: the maximum number of objects to index in a task
    update_only: don't necessarily index *everything*. Honour the SearchIndex's .update_filter() method if present.
    """
    haystack_connections = loading.ConnectionHandler(settings.HAYSTACK_CONNECTIONS)
    backends = haystack_connections.connections_info.keys()
    for label in haystack_load_apps():
        for using in backends:
            unified_index = haystack_connections[using].get_unified_index()
            for model in haystack_get_models(label):
                try:
                    index = unified_index.get_index(model)
                except NotHandled:
                    continue

                qs = index.build_queryset(using=using)

                if update_only and hasattr(index, 'update_filter'):  # allow updating of only-likely-changing instances
                    qs = index.update_filter(qs)

                tasks = []
                for group in grouper(qs.values('pk'), group_size):
                    if use_celery:
                        from coredata.tasks import update_index_chunk as update_index_chunk_task
                        t = update_index_chunk_task.si(using=using, model=model, pks=[o['pk'] for o in group])
                        tasks.append(t)
                    else:
                        update_index_chunk(using=using, model=model, pks=[o['pk'] for o in group])

                if use_celery:
                    import celery
                    chain = celery.chain(*tasks)
                    chain.delay()


def update_index_chunk(using: str, model: Type[models.Model], pks: Iterable[int], commit: bool = True) -> None:
    """
    Index these instances (type model, primary keys in pks) with Haystack.
    """
    haystack_connections = loading.ConnectionHandler(settings.HAYSTACK_CONNECTIONS)
    backend = haystack_connections[using].get_backend()
    unified_index = haystack_connections[using].get_unified_index()
    index = unified_index.get_index(model)
    qs = model.objects.filter(pk__in=pks)
    backend.update(index, qs, commit=commit)


def our_clear_index(commit: bool = True) -> None:
    backend_names = connections.connections_info.keys()
    for backend_name in backend_names:
        backend = connections[backend_name].get_backend()
        backend.clear(commit=commit)
