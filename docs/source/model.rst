=====
Model
=====

The `model` package contains

* The :py:class:`Backends` extension providing the infrastructure to
  use multiple backends
* The implementations of such backends in the sub-packages.

Backends
--------

This is automatically generated documentation from  the `sipa.model` package.

.. automodule:: sipa.model
   :members:
   :exclude-members: Backends

.. autoclass:: Backends
   :members:
   :undoc-members:

.. data:: backends

   A proxy pointing to the curent app's :py:data:`backends` object.


Datasource
----------

Sipa distinguishes between two concepts:

* A *Datasource* is the technical entity providing data, such as the
  user class, the mail server, etc.
* A *Dormitory* is the entity that should be displayed as an option on
  the login field.  Therefore, its most important property is the
  `display_name` and the datasource it belongs to.  Also, it holds information about the IP
  subnets, since these are bound to a location, and not the technical backend.

.. automodule:: sipa.model.datasource
   :member-order: bysource
   :members:
   :undoc-members:


User
----

.. automodule:: sipa.model.user
   :member-order: groupwise
   :members:
   :undoc-members:


Property
--------

.. automodule:: sipa.model.fancy_property
   :members:
   :undoc-members:
