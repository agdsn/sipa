import pkgutil
import typing

import icalendar
import pytest


from sipa.utils import events_from_calendar, Event, xss_location


@pytest.fixture(scope='session')
def ical_data():
    # test calendar data. cURLed and truncated to one `VEVENT` block.
    return pkgutil.get_data(__package__, "./example_calendar.ical")


@pytest.fixture(scope='session')
def calendar(ical_data: str) -> icalendar.Calendar:
    return icalendar.Calendar.from_ical(ical_data)


def test_ical_conversion(calendar: icalendar.Calendar, time_machine):
    time_machine.move_to("2023-05-20")
    events = events_from_calendar(calendar)
    assert len(events) == 1
    [ev] = events
    assert isinstance(ev, icalendar.Event)
    ev: Event = typing.cast(Event, ev)
    assert ev['SUMMARY'] == "Teamsitzung Computing"
    assert ev['LOCATION'] == "NOC, Räcknitzhöhe 35"
    assert ev["DTSTART"].dt.weekday() == 1  # tuesday
    assert ev["DTEND"].dt.weekday() == 1  # tuesday


def test_xss():
    assert(xss_location("[123](http://example.com)")) == "[123](http://example.com)"
    assert(xss_location("123")) == "123"
    assert(xss_location("[123](https://example.com), 234")) == "[123](https://example.com), 234"
    assert(xss_location("")) == "-"

    assert(xss_location("[123] (http://example.com)")) == "-"
    assert(xss_location("https://example.com")) == "-"
    assert(xss_location("[123]")) == "-"
    assert(xss_location("[<h1>123</h1>](https://example.com)")) == "-"
    assert(xss_location("123, <h1>123</h1>(https://example.com)")) == "123"
    assert(xss_location("[<h1>123</h1>](https://example.com ), 123, [234](https://<h1>123</h1>)")) == "123"
