from django.utils.functional import lazy
from coredata.models import Semester
import datetime
import intervaltree

ONE_DAY = datetime.timedelta(days=1)
def _build_semester_lookup():
    """
    Build data structure to let us easily look up date -> strm.
    """
    all_semesters = Semester.objects.all()
    intervals = ((s.name, Semester.start_end_dates(s)) for s in all_semesters)
    intervals = (
        intervaltree.Interval(st, en+ONE_DAY, name)
        for (name, (st, en)) in intervals)
    return intervaltree.IntervalTree(intervals)

# lazy here avoids db queries in tests before the test environment is initialized
semester_lookup = lazy(_build_semester_lookup)()
STRM_MAP = lazy(lambda: dict((s.name, s) for s in Semester.objects.all()))()
