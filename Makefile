.PHONY: run extract_messages update_messages translate docs show_docs

run:
	docker-compose -f build/development.yml up -d
extract_messages:
	pybabel extract -F babel.cfg -k lazy_gettext \
		--project=sipa \
		--msgid-bugs-address='du-bist-gefragt (at) agdsn.de' \
		--copyright-holder="AG DSN" \
		--version=$(shell git describe) \
		--no-location \
		--no-wrap \
		-o messages.pot ./
update_messages:
	pybabel update \
		-i messages.pot \
		--update-header-comment \
		--no-wrap \
		-d sipa/translations/
translate: extract_messages update_messages
	# dirty hack to set the source language
	sed -e '/Generated-By/a "X-Source-Language: de"' \
		-i sipa/translations/en/LC_MESSAGES/messages.po
	poedit sipa/translations/en/LC_MESSAGES/messages.po
	pybabel compile -d sipa/translations/

docs-clean:
	$(MAKE) -C docs clean

docs:
	sphinx-apidoc -o docs/source/ref sipa
	$(MAKE) -C docs html

show_docs:
	cd docs/build/html && python -m http.server
