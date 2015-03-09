#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Blueprint, render_template, session, abort
from jinja2.exceptions import TemplateNotFound
from flatpages import pages as flat_pages


bp_pages = Blueprint('pages', __name__, url_prefix='/pages')


#def content_localization(template, **kwargs):
    #"""Some content pages are not suitable to be translated string by string.
    #In this case we use the whole template in dual language, one template
    #for german, one for english text.
    #This method can switch the output template by looking up the language
    #setting in the session.

    #If the english template is not found (not yet translated) it will
    #return the german version (lets hope this one's available).
    #"""
    #if 'lang' in session and session['lang'] == 'en':
        #try:
            #return render_template("content/en/" + template, **kwargs)
        #except TemplateNotFound:
            #pass
    #return render_template("content/" + template, **kwargs)


#@bp_pages.route("/contacts")
#def contacts():
    #return render_template("content/ansprechpartner.html")


#@bp_pages.route("/traffic")
#def traffic():
    #return content_localization("traffic.html")


@bp_pages.route('/', defaults={'page': 'index'})
@bp_pages.route('/<page>')
def show(page):
    lang = session.get('lang', 'de')
    print lang
    flat_pages.reload()
    try:
        #page = filter(lambda p: p.path.startswith(lang + u'/'+ page), flat_pages)[0]
        page = filter(lambda p: p.path.startswith(lang + u'/' + page), flat_pages)[0]
        return render_template('template.html', page = page)
    except TemplateNotFound:
        flash(gettext(u"Seite nicht gefunden!"), "warning")
    except:
        abort(404)