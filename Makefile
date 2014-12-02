translate:
	pybabel extract -F babel.cfg -o messages.pot ./
	pybabel update -i messages.pot -d translations/
	poedit translations/en/LC_MESSAGES/messages.po
	pybabel compile -d translations/
