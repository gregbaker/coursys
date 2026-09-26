from django.db import models

from coredata.models import Member
from grades.models import Activity, NumericActivity, NumericGrade


ATTENDANCE_CHOICES = [
    ("NO", "absent"),
    ("YES", "present"),
]


class Attendance(models.Model):
    student = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="+")
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name="+")
    marker = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(
        max_length=3, null=False, blank=False, choices=ATTENDANCE_CHOICES, default="NO"
    )

    class Meta:
        unique_together = [
            ("student", "activity"),
        ]

    def __str__(self):
        return f"{self.student.person.userid}, {self.activity.name}: {self.status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create a corresponding AttendanceChange object
        ac = AttendanceChange(student=self.student, activity=self.activity, marker=self.marker, status=self.status)
        ac.save()
        # And update any downstream grades
        self.update_linked_grades()

    def update_linked_grades(self):
        try:
            numeric_activity = NumericActivity.objects.get(id=self.activity_id)
            if self.activity.attendance() == 'THIS':
                try:
                    g = NumericGrade.objects.get(activity=numeric_activity, member=self.student)
                except NumericGrade.DoesNotExist:
                    g = NumericGrade(activity=numeric_activity, member=self.student, flag='GRAD')
                if g.flag == 'GRAD':
                    g.value = numeric_activity.max_grade
                    g.save(entered_by=self.marker.person)

        except NumericActivity.DoesNotExist:
            pass

        sum_activities = [
            a for a in 
            NumericActivity.objects.filter(offering=self.activity.offering)
            if a.attendance() == 'SUM'
        ]
        if sum_activities:
            total = Attendance.objects.filter(activity__offering=self.activity.offering, student=self.student, status='YES').count()
            for a in sum_activities:
                try:
                    g = NumericGrade.objects.get(activity=a, member=self.student)
                    if g.flag != 'CALC':
                        continue
                except NumericGrade.DoesNotExist:
                    g = NumericGrade(activity=a, member=self.student, flag='CALC')

                g.value = total
                g.save(entered_by=self.marker.person)


class AttendanceChange(models.Model):
    student = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="+")
    activity = models.ForeignKey(
        Activity,
        on_delete=models.PROTECT,
        related_name="+",
    )
    marker = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="+")
    status = models.CharField(
        max_length=3, null=False, blank=False, choices=ATTENDANCE_CHOICES
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return (
            f"{self.student.username} {self.activity.name} changed "
            f"at {self.changed_at:%Y-%m-%d %H:%M:%S}"
        )
