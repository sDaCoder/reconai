from datetime import datetime


def calculate_date_difference(date1, date2):

    if isinstance(date1, str):
        date1 = datetime.fromisoformat(date1)

    if isinstance(date2, str):
        date2 = datetime.fromisoformat(date2)

    difference = abs(date2 - date1)

    return difference.days
