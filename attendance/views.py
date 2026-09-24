from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from attendance.models import Attendance
from coredata.models import CourseOffering, Member
from courselib.auth import requires_course_staff_by_slug
from grades.models import Activity


@requires_course_staff_by_slug
def take(request: HttpRequest, course_slug: str, activity_slug: str) -> HttpResponse:
    offering = get_object_or_404(CourseOffering, slug=course_slug)
    activity = get_object_or_404(
        Activity, offering=offering, slug=activity_slug, deleted=False
    )

    attendances = Attendance.objects.filter(activity=activity).select_related('student__person')
    students = Member.objects.filter(offering=offering, role='STUD').select_related('person')

    context = {
        "offering": offering,
        "activity": activity,
        "students": students,
    }
    return render(request, "attendance/take.html", context)
