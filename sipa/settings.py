from sipa.config import FLASK_SECRET_KEY

SECRET_KEY = FLASK_SECRET_KEY

LOG_FILE = 'error.log'

FLATPAGES_EXTENSION = '.md'
FLATPAGES_MARKDOWN_EXTENSIONS = [
    'sane_lists',
    'sipa.utils.bootstraped_tables',
    'nl2br',
    'meta'
]
