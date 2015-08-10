# -*- coding: utf-8 -*-
import os

model_name = os.getenv('SIPA_MODEL', 'sample')

module = __import__('{}.{}.user'.format(__name__, model_name),
                    fromlist='{}.{}'.format(__name__, model_name))

init_context = module.init_context
User = module.User
query_gauge_data = module.query_gauge_data
