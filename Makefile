.PHONY: run translate docs show_docs

run:
	docker-compose -f build/development.yml up -d
translate:
	pybabel extract -F babel.cfg -k lazy_gettext \
		--project=sipa \
		--msgid-bugs-address='du-bist-gefragt (at) agdsn.de' \
		--copyright-holder="AG DSN" \
		--version=$(shell git describe) \
		--no-location \
		-o messages.pot ./
	pybabel update -i messages.pot --update-header-comment -d sipa/translations/
	# dirty hack to set the source language
	sed -e '/Generated-By/a "X-Source-Language: de"' \
		-i sipa/translations/en/LC_MESSAGES/messages.po
	poedit sipa/translations/en/LC_MESSAGES/messages.po
	pybabel compile -d sipa/translations/

docs:
	$(MAKE) -C docs html

show_docs:
	cd docs/build/html && python -m http.server
