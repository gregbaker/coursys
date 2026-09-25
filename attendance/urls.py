from django.urls import re_path as url

from courselib.urlparts import USERID_SLUG
from . import views as attendance_views

attendance_patterns = [ # prefix /COURSE_SLUG/attendance/
    url(r'^$', attendance_views.take, name='take'),
    url(rf'^set/{USERID_SLUG}$', attendance_views.set, name='set'),
]
