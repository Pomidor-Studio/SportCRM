from __future__ import annotations

from datetime import date, timedelta
from itertools import cycle
from typing import Generator, List, NewType

Weekdays = NewType('Weekdays', List[int])
Weekdays.__doc__ = \
    """List of weekdays, in natural order, monday first"""


def get_nearest_to(
    required_day: date,
    allowed_days: Weekdays,
    end_date: date = None
) -> date:
    if end_date is not None and required_day >= end_date:
        raise ValueError("Can't find next event for date in future")

    r_dayw = required_day.weekday()
    # Find all days that are after required date
    next_days = [x for x in allowed_days if x > r_dayw]

    # If we have some day in event class, we are sure than in distance
    # more than one week will be new event
    # So, we check edge case if required_day is in last week of
    # event class
    if end_date is not None and (end_date - required_day) < timedelta(days=7):
        if not len(next_days):
            raise ValueError("Required day is out of event class date range")

        nearest_day = next_days[0]
    else:
        # If required date was after last weekday event, use first week day
        try:
            nearest_day = next_days[0]
        except IndexError:
            nearest_day = allowed_days[0]

    delta = (nearest_day - r_dayw) % 7 if nearest_day != r_dayw else 7
    return required_day + timedelta(days=delta)


def days_delta(days) -> List[int]:
    """
    Get list of days delta between event occurrences. Can work with
    shifted days (monday is not first day in list)

    For [0, 2, 4] it will return [2, 2, 3]
    For [0, 1, 2, 3, 4, 5, 6] it will return [1, 1, 1, 1, 1, 1, 1]
    """
    deltas = [0] * len(days)

    if not(len(days)):
        return deltas

    for x in range(len(days)):
        if x == len(days) - 1:
            deltas[x] = 7 - days[x] + days[0]
        else:
            deltas[x] = days[x+1] - days[x]

    return deltas


def next_day(
    start: date,
    stop: date,
    days: Weekdays
) -> Generator[date, None, None]:
    """
    Next date for event class generator

    :param start: Date of initial period
    :param stop: Date of end period
    :param days: List of allowed week days, in natural order

    :return: Next date of event
    """
    if start > stop:
        raise ValueError('Start of period is greater than end date')

    delta_days = days_delta(days)

    current = start
    cur_wd = current.weekday()

    if cur_wd not in days:
        try:
            current = get_nearest_to(current, days, stop)
        except ValueError:
            return
        cur_wd = current.weekday()

    current_widx = days.index(cur_wd)
    if current_widx != 0:
        # First date of period is in middle of week - shift days and deltas
        delta_days = delta_days[current_widx:] + delta_days[:current_widx]

    rr_deltas = cycle(delta_days)

    while current <= stop:
        yield current
        current += timedelta(days=next(rr_deltas))
