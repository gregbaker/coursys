from django.urls import re_path as url
from . import views as attendance_views

attendance_patterns = [ # prefix /COURSE_SLUG/attendance/
    url(r'^$', attendance_views.take, name='take'),
]
