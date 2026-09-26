from django.test import TestCase

from attendance.models import Attendance
from coredata.models import CourseOffering, Member
from courselib.testing import TEST_COURSE_SLUG, Client, test_views
from grades.models import NumericActivity, NumericGrade


class AttendanceTest(TestCase):
    fixtures = ["basedata", "coredata"]

    def test_pages(self):
        c = Client()
        c.login_user("ggbaker")
        test_views(
            self,
            c,
            "offering:attendance:",
            ["take"],
            {"course_slug": TEST_COURSE_SLUG, "activity_slug": "a1"},
        )

    def test_grade_propogation(self):
        """
        Test the logic for attendance -> grades where configured.
        """
        offering = CourseOffering.objects.get(slug=TEST_COURSE_SLUG)
        offering.set_attendance(True)
        offering.save()

        sum_act = NumericActivity(
            offering=offering,
            name="Attendance",
            short_name="Att",
            max_grade=3,
            percent=1,
            position=99,
        )
        sum_act.set_attendance("SUM")
        sum_act.save()

        a1 = NumericActivity.objects.get(offering=offering, slug="a1")
        a1.set_attendance("THIS")
        a1.save()
        a2 = NumericActivity.objects.get(offering=offering, slug="a2")
        a3 = NumericActivity.objects.get(offering=offering, slug="exam")

        s1, s2 = Member.objects.filter(offering=offering, role="STUD")[0:2]
        inst = Member.objects.filter(offering=offering, role="INST")[0]

        # Assuming the marking is empty...
        self.assertEqual(NumericGrade.objects.filter(member=s1).count(), 0)
        self.assertEqual(NumericGrade.objects.filter(member=s2).count(), 0)

        # s1 gets some history to make sure it's replaced
        NumericGrade(activity=a1, member=s1, value=99, flag="GRAD").save(
            entered_by=inst.person
        )
        NumericGrade(activity=a2, member=s1, value=99, flag="GRAD").save(
            entered_by=inst.person
        )
        NumericGrade(activity=sum_act, member=s1, value=99, flag="CALC").save(
            entered_by=inst.person
        )

        # they attended both a1 and a2
        Attendance(activity=a1, student=s1, status="YES", marker=inst).save()
        Attendance(activity=a1, student=s2, status="YES", marker=inst).save()
        Attendance(activity=a2, student=s1, status="YES", marker=inst).save()
        Attendance(activity=a2, student=s2, status="YES", marker=inst).save()
        Attendance(activity=a3, student=s1, status="NO", marker=inst).save()
        Attendance(activity=a3, student=s2, status="YES", marker=inst).save()

        self.assertEqual(
            NumericGrade.objects.get(activity=a1, member=s1).value, a1.max_grade
        )
        self.assertEqual(NumericGrade.objects.get(activity=a2, member=s1).value, 99)
        self.assertEqual(NumericGrade.objects.get(activity=sum_act, member=s1).value, 2)

        self.assertEqual(
            NumericGrade.objects.get(activity=a1, member=s2).value, a1.max_grade
        )
        self.assertEqual(NumericGrade.objects.filter(activity=a2, member=s2).count(), 0)
        self.assertEqual(NumericGrade.objects.get(activity=sum_act, member=s2).value, 3)
