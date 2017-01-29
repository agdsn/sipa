.PHONY: run translate docs show_docs

run:
	docker-compose -f build/development.yml up -d
translate:
	pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot ./
	pybabel update -i messages.pot -d sipa/translations/
	poedit sipa/translations/en/LC_MESSAGES/messages.po
	pybabel compile -d sipa/translations/

docs:
	$(MAKE) -C docs html

show_docs:
	cd docs/build/html && python -m http.server
