from factory.alchemy import SQLAlchemyModelFactory as Factory
from factory import Faker, LazyAttribute, Sequence, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDecimal, FuzzyText

from sipa.model.wu.database_utils import STATUS, ACTIVE_STATUS
from sipa.model.wu.schema import (db, DORMITORY_MAPPINGS, Nutzer,
                                  Computer, Credit, Traffic)
from sipa.utils import timetag_today


class WuFactory(Factory):
    class Meta:
        sqlalchemy_session = db.session


class NutzerFactory(WuFactory):
    class Meta:
        model = Nutzer

    nutzer_id = Sequence(lambda n: n)
    wheim_id = FuzzyInteger(0, len(DORMITORY_MAPPINGS) - 1)
    etage = FuzzyInteger(1, 15)
    zimmernr = FuzzyInteger(11, 55)
    unix_account = Sequence(lambda n: "user{}".format(n))
    status = FuzzyChoice(STATUS.keys())
    internet_by_rental = False


class ActiveNutzerFactory(NutzerFactory):
    status = FuzzyChoice(ACTIVE_STATUS)


class InactiveNutzerFactory(NutzerFactory):
    status = FuzzyChoice(set(STATUS.keys()) - set(ACTIVE_STATUS))


class UnknownStatusNutzerFactory(NutzerFactory):
    status = FuzzyChoice(set(range(20)) - set(STATUS.keys()))


class ComputerFactory(WuFactory):
    class Meta:
        model = Computer

    nutzer = SubFactory(NutzerFactory)
    nutzer_id = LazyAttribute(lambda self: self.nutzer.nutzer_id)

    c_etheraddr = Faker('mac_address')
    c_ip = Faker('ipv4')
    c_hname = FuzzyText()
    c_alias = FuzzyText()


class NoHostAliasComputerFactory(ComputerFactory):
    c_alias = None


class CreditFactory(WuFactory):
    class Meta:
        model = Credit

    nutzer = SubFactory(NutzerFactory)
    user_id = LazyAttribute(lambda self: self.nutzer.nutzer_id)
    amount = FuzzyInteger(low=0, high=63*1024*1024)
    timetag = FuzzyInteger(low=timetag_today() - 21,
                           high=timetag_today())


class TrafficFactory(WuFactory):
    class Meta:
        model = Traffic
    # TODO: `unique` constraint not met
    timetag = FuzzyInteger(low=timetag_today() - 21,
                           high=timetag_today())
    ip = Faker('ipv4')
    input = FuzzyDecimal(low=0, high=10*1024*1024)
    output = FuzzyDecimal(low=0, high=10*1024*1024)
