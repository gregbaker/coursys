from django.db import models

from coredata.models import Member
from grades.models import Activity


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

    def save_change(self) -> None:
        """
        Create a corresponding AttendanceChange object
        """
        ac = AttendanceChange(student=self.student, activity=self.activity, marker=self.marker, status=self.status)
        ac.save()


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
