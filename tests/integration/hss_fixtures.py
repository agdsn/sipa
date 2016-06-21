from collections import OrderedDict
from datetime import date


from sipa.model.hss.schema import Account, AccountProperty, Access, IP, Mac, TrafficLog


class HSSOneAccountFixture:
    @property
    def fixtures_pg(self):
        return OrderedDict([
            (Account, [
                Account(
                    account='sipatinator',
                    name="Sipa Tinator",
                    traffic_balance=63*1024**3,
                    access_id=1,
                ),
            ]),
            (AccountProperty, [
                AccountProperty(
                    account='sipatinator',
                    active=False,
                ),
            ]),
            (Access, [
                Access(
                    id=1,
                    building="HSS46",
                    floor="0",
                    flat="1",
                    room="b",
                )
            ]),
            (IP, [
                IP(ip="141.30.234.15", account="sipatinator"),
                IP(ip="141.30.234.16"),
                IP(ip="141.30.234.18", account="sipatinator"),
            ]),
            (Mac, [
                Mac(id=1, mac="aa:bb:cc:ff:ee:dd"),
                Mac(id=2, mac="aa:bb:cc:ff:ee:de", account='sipatinator'),
                Mac(id=3, mac="aa:bb:cc:ff:ee:df", account='sipatinator'),
            ]),
        ])


class HSSOneTrafficAccountFixture(HSSOneAccountFixture):
    @property
    def fixtures_pg(self):
        return OrderedDict([
            *super().fixtures_pg.items(),
            (TrafficLog, [
                TrafficLog(id=1, account='sipatinator', date=date(2016, 4, 24),
                           bytes_in=3657658, bytes_out=20646),
                TrafficLog(id=2, account='sipatinator', date=date(2016, 4, 25),
                           bytes_in=3354878, bytes_out=11146),
                TrafficLog(id=3, account='sipatinator', date=date(2016, 4, 26),
                           bytes_in=3653478, bytes_out=65746),
                TrafficLog(id=4, account='sipatinator', date=date(2016, 4, 27),
                           bytes_in=1118758, bytes_out=11546),
                TrafficLog(id=5, account='sipatinator', date=date(2016, 4, 28),
                           bytes_in=1957368, bytes_out=32246),
                TrafficLog(id=6, account='sipatinator', date=date(2016, 4, 29),
                           bytes_in=9455668, bytes_out=31686),
                TrafficLog(id=7, account='sipatinator', date=date(2016, 4, 30),
                           bytes_in=9851368, bytes_out=42146),
                TrafficLog(id=8, account='sipatinator', date=date(2016, 5, 1),
                           bytes_in=7318688, bytes_out=31556),
            ]),
        ])


class HSSOneTrafficAccountDaysMissingFixture(HSSOneTrafficAccountFixture):
    @property
    def fixtures_pg(self):
        old_traffic_logs = super().fixtures_pg.pop(TrafficLog)
        return OrderedDict([
            *super().fixtures_pg.items(),
            (TrafficLog, [
                *old_traffic_logs[:5],
            ]),
        ])


class HSSAccountsWithPropertiesFixture:
    @property
    def fixtures_pg(self):
        return OrderedDict([
            (Account, [
                Account(
                    account='sipatinator',
                    name="Sipa Tinator",
                    traffic_balance=63*1024**3,
                ),
                Account(
                    account='active_user',
                    name="Active user",
                    traffic_balance=63*1024**3,
                ),
            ]),
            (AccountProperty, [
                AccountProperty(
                    account='sipatinator',
                    active=False,
                ),
                AccountProperty(
                    account='active_user',
                    active=True,
                )
            ]),
        ])


class FrontendFixture(HSSOneTrafficAccountFixture):
    """Fixture aiming to provide anything necessary for hss frontend tests
    to work.
    """
    pass
