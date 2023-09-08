from datetime import timedelta

from utils.models import RecurrenceFrequency


def recurrence_date_generator(start_date, recurrence):
    current_date = start_date
    while True:
        if recurrence == RecurrenceFrequency.WEEKLY:
            current_date = current_date + timedelta(days=7)
        else:
            raise ValueError("Invalid recurrence frequency")
        yield current_date
