from flask.ext.flatpages import FlatPages
#workaround found here http://stackoverflow.com/questions/11020170/using-flask-extensions-in-flask-blueprints
# because we want to use flatpages within blueprints

pages = FlatPages()
