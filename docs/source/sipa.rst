======
`sipa`
======

The `sipa` package contains everything – things that are not grouped in
subpackages are mainly frontend-related.

`.blueprints`
-------------
The :mod:`sipa.blueprints` package contains the actual endpoint definitions.
For an overview of flask blueprints, refer to the :ref:`flask documentation <flask:blueprints>`.


`.flatpages`
------------

The :mod:`sipa.flatpages` module provides the :class:`~sipa.flatpages.CategorizedFlatPages`
flask extension, which is based on :mod:`Flask-FlatPages <ffp:flask_flatpages>`.