translate:
	pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot ./
	pybabel update -i messages.pot -d sipa/translations/
	poedit sipa/translations/en/LC_MESSAGES/messages.po
	pybabel compile -d sipa/translations/
