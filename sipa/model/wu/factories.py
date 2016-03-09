from random import randint

from factory.alchemy import SQLAlchemyModelFactory as Factory
from factory import Faker, LazyAttribute, Sequence, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from sipa.model.wu.database_utils import ACTIVE_STATUS
from sipa.model.wu.schema import db, DORMITORY_MAPPINGS, Nutzer, Computer


class WuFactory(Factory):
    class Meta:
        sqlalchemy_session = db.session


class NutzerFactory(WuFactory):
    class Meta:
        model = Nutzer

    nutzer_id = Sequence(lambda n: n)
    wheim_id = LazyAttribute(lambda n: randint(0, len(DORMITORY_MAPPINGS)-1))
    etage = LazyAttribute(lambda _: randint(1, 15))
    zimmernr = LazyAttribute(lambda _: "{}{}".format(randint(1, 5), randint(1, 3)))
    unix_account = Sequence(lambda n: "user{}".format(n))
    status = 0


class ActiveNutzerFactory(NutzerFactory):
    status = FuzzyChoice(ACTIVE_STATUS)


class InactiveNutzerFactory(NutzerFactory):
    status = FuzzyChoice(set(range(20)) - set(ACTIVE_STATUS))


class ComputerFactory(WuFactory):
    class Meta:
        model = Computer

    nutzer = SubFactory(NutzerFactory)
    nutzer_id = LazyAttribute(lambda self: self.nutzer.nutzer_id)

    c_etheraddr = Faker('mac_address')
    c_ip = Faker('ipv4')
    c_hname = FuzzyText()
    c_alias = FuzzyText()
