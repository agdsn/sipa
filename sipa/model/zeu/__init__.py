# -*- coding: utf-8 -*-

from ..datasource import PrematureDataSource, Dormitory


datasource = PrematureDataSource(
    name='zeu',
    website_url="https://zeus.wh25.tu-dresden.de",
    support_mail="agdsn@wh25.tu-dresden.de",
)

dormitories = [Dormitory(
    name='zeu',
    display_name="Zeunerstraße",
    datasource=datasource,
)]
