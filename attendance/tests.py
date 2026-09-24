from django.test import TestCase

from courselib.testing import TEST_COURSE_SLUG, Client, test_views

class AttendanceTest(TestCase):
    fixtures = ['basedata', 'coredata']

    def test_pages(self):
        """
        Basic page rendering
        """
        c = Client()
        c.login_user('ggbaker')
        test_views(self, c, 'offering:attendance:', ['take'], {'course_slug': TEST_COURSE_SLUG, 'activity_slug': 'a1'})
