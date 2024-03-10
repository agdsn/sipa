from functools import wraps
from textwrap import dedent

from flask import make_response, request, render_template_string


# TODO proper type hinting: require `-> str`
def htmx_fragment(viewfunc):
    @wraps(viewfunc)
    def _wrapped(*a, **kw):
        resp = make_response(viewfunc(*a, **kw))
        if request.headers.get("Hx-Request") == "true":
            return resp
        resp.data = render_template_string(
            dedent("""\
            {% extends "base.html" %}
            {% block content %}<div class="row">{{ content | safe }}</div>{% endblock %}
        """),
            content=resp.data.decode(),
        ).encode()
        return resp

    return _wrapped
