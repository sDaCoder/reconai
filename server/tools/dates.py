from datetime import datetime, timezone


def calculate_date_difference(date1, date2):

    if isinstance(date1, str):
        date1 = datetime.fromisoformat(date1)

    if isinstance(date2, str):
        date2 = datetime.fromisoformat(date2)

    if date1.tzinfo is None and date2.tzinfo is not None:
        date1 = date1.replace(tzinfo=timezone.utc)
    elif date2.tzinfo is None and date1.tzinfo is not None:
        date2 = date2.replace(tzinfo=timezone.utc)

    difference = abs(date2 - date1)

    return difference.days
