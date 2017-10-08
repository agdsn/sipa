from factory.alchemy import SQLAlchemyModelFactory as Factory
from factory import Faker, LazyAttribute, Sequence, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDecimal, FuzzyText

from sipa.model.wu.database_utils import STATUS, ACTIVE_STATUS
from sipa.model.wu.schema import (db, Nutzer, Wheim, Computer, Credit, Traffic)
from sipa.utils import timetag_today


class WuFactory(Factory):
    class Meta:
        sqlalchemy_session = db.session


class WheimFactory(WuFactory):
    class Meta:
        model = Wheim
    wheim_id = Sequence(lambda n: n)
    str = FuzzyText(suffix='straße')
    hausnr = FuzzyChoice(str(x) for x in range(1, 15))


class NutzerFactory(WuFactory):
    class Meta:
        model = Nutzer

    nutzer_id = Sequence(lambda n: n)
    name = FuzzyChoice({"Peterson", "Schmidt Wolf", "Huang"})
    vname = FuzzyChoice({"Lee", "Lars", "Daniel Garcia"})
    wheim = SubFactory(WheimFactory)
    etage = FuzzyInteger(1, 15)
    zimmernr = FuzzyChoice(str(x) for x in range(11, 56))
    unix_account = Sequence(lambda n: "user{}".format(n))
    status = FuzzyChoice(STATUS.keys())
    internet_by_rental = False
    use_cache = False


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
