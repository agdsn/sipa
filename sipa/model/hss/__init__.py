# -*- coding: utf-8 -*-

from ..datasource import PrematureDataSource, Dormitory


datasource = PrematureDataSource(
    name='hss',
    display_name="Hochschulstraße",
    website_url="https://wh12.tu-dresden.de",
    support_mail="support@wh12.tu-dresden.de",
)

dormitories = [Dormitory(
    name='hss',
    display_name="Hochschulstraße",
    datasource=datasource,
)]
