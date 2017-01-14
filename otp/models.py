# based on http://stackoverflow.com/a/4631504/1236542

import sys

from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.signals import user_logged_in, user_logged_out

from django.db.models.signals import post_save
from django.utils import timezone

NEVER_AUTH = 100000 #sys.maxint

class SessionInfo(models.Model):
    session_key = models.CharField(max_length=40, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    last_auth = models.DateTimeField(null=True)
    last_2fa = models.DateTimeField(null=True)

    @classmethod
    def for_session_key(cls, session_key, save_new=True):
        try:
            si = cls.objects.get(session_key=session_key)
        except (SessionInfo.DoesNotExist):
            si = SessionInfo(session_key=session_key)
            if save_new:
                si.save()

        return si

    @classmethod
    def for_request(cls, request, save_new=True):
        if hasattr(request, 'session_info') and request.session_info is not None:
            return request.session_info

        if request.session.session_key is None:
            return None

        si = cls.for_session_key(request.session.session_key, save_new=save_new)

        request.session_info = si
        return si

    @classmethod
    def just_logged_in(cls, request):
        si = cls.for_request(request, save_new=False)
        si.last_auth = timezone.now()
        si.save()
        return si

    @classmethod
    def just_logged_out(cls, request):
        si = cls.for_request(request, save_new=False)
        si.last_auth = None
        si.save()
        return si

    def __unicode__(self):
        return '%s@%s' % (self.session, self.created)

    def age(self):
        'Age of the session, in seconds.'
        return (timezone.now() - self.created)

    def age_auth(self):
        'Age of the standard authentication on the session, in seconds.'
        return (timezone.now() - self.last_auth) if self.last_auth else NEVER_AUTH

    def age_2fa(self):
        'Age of the second-factor authentication on the session, in seconds.'
        return (timezone.now() - self.last_2fa) if self.last_2fa else NEVER_AUTH



def logged_in_listener(request, **kwargs):
    SessionInfo.just_logged_in(request)

def logged_out_listener(request, **kwargs):
    SessionInfo.just_logged_out(request)

user_logged_in.connect(logged_in_listener)
user_logged_out.connect(logged_out_listener)

def session_create_listener(instance, **kwargs):
    instance.session_info = SessionInfo.for_session_key(instance.session_key)

post_save.connect(session_create_listener, sender=Session)