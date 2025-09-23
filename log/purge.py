from courselib.purge import DataPurger
from log.models import LogEntry

class LogEntryPurger(DataPurger):
    model_class = LogEntry

    def purge_queryset(self):
        return LogEntry.objects.filter(datetime__lt=self.age(365))