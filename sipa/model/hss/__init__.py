# -*- coding: utf-8 -*-

from ..datasource import PrematureDataSource, Dormitory


datasource = PrematureDataSource(
    name='hss',
    website_url="https://wh12.tu-dresden.de",
    # to be included when it becomes a DataSource
    # webmailer_url="https://wh12.tu-dresden.de/roundcube/",
    support_mail="support@wh12.tu-dresden.de",
)

dormitories = [Dormitory(
    name='hss',
    display_name="Hochschulstraße",
    datasource=datasource,
)]
