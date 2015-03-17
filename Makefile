translate:
	pybabel extract -F babel.cfg -o messages.pot ./
	pybabel update -i messages.pot -d sektionsweb/translations/
	poedit sektionsweb/translations/en/LC_MESSAGES/messages.po
	pybabel compile -d sektionsweb/translations/
