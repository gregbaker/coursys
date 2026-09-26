import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader

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
    attendance_dict = {a.student.person.userid: a for a in attendances}

    students = Member.objects.filter(offering=offering, role='STUD').select_related('person')
    student_data = [(s, attendance_dict.get(s.person.userid, Attendance(student=s, activity=activity))) for s in students]

    context = {
        "offering": offering,
        "activity": activity,
        "student_data": student_data,
    }
    return render(request, "attendance/take.html", context)

@requires_course_staff_by_slug
def set(request: HttpRequest, course_slug: str, activity_slug: str, userid: str) -> HttpResponse:
    offering = get_object_or_404(CourseOffering, slug=course_slug)
    activity = get_object_or_404(
        Activity, offering=offering, slug=activity_slug, deleted=False
    )
    student = get_object_or_404(Member, offering=offering, person__userid=userid, role="STUD")
    marker = get_object_or_404(Member, offering=offering, person__userid=request.user.username, role__in=["INST", "TA"])

    try:
        a = Attendance.objects.get(student=student, activity=activity)
    except Attendance.DoesNotExist:
        a = Attendance(student=student, activity=activity)
    a.marker = marker
    a.status = "YES" if request.POST.get('status', 'NO') == 'YES' else "NO"
    a.save()
    a.save_change()

    context = {
        "offering": offering,
        "activity": activity,
        "userid": userid,
        "status": a.status
    }
    response = render(request, "attendance/_buttons.html", context)
    word = 'present' if a.status == 'YES' else 'absent'
    response["HX-Trigger"] = json.dumps({'showSaved': f'Status saved: {student.person.name()} {word}.'})
    return response


@requires_course_staff_by_slug
def refresh(request: HttpRequest, course_slug: str, activity_slug: str) -> HttpResponse:
    offering = get_object_or_404(CourseOffering, slug=course_slug)
    activity = get_object_or_404(
        Activity, offering=offering, slug=activity_slug, deleted=False
    )

    attendances = Attendance.objects.filter(activity=activity).select_related('student__person')
    attendance_dict = {a.student.person.userid: a for a in attendances}

    students = Member.objects.filter(offering=offering, role='STUD').select_related('person')
    student_data = [(s, attendance_dict.get(s.person.userid, Attendance(student=s, activity=activity))) for s in students]
    htmx_data = {f"#buttons-{s.person.userid}": loader.render_to_string("attendance/_buttons.html", {
        "offering": offering,
        "activity": activity,
        "userid": s.person.userid,
        "status": a.status
    }, request=request) for s, a in student_data}

    return JsonResponse(htmx_data)