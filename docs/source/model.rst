=====
Model
=====

The :mod:`sipa.model` package mainly contains:

#. :class:`~sipa.backends.datasource.Datasource` implementations for the
   :py:mod:`sipa.backends` extension and everything that comes with it
   (such as database setups)
#. An abstract :class:`BaseUser` class which defines all the properties a
   backend's user should provide.
#. Related to the second, a smart property-like type which is able to express
   whether a particular property is “supported” or not and whether it allows
   for editing and / or deleting.


Implemented backends
--------------------

Sipa registers the following datasources:

.. autodata:: sipa.model.AVAILABLE_DATASOURCES
   :noindex:

Their implementations are in the corresponding modules

* :mod:`sipa.model.hss`
* :mod:`sipa.model.pycroft`
* :mod:`sipa.model.sample`


User
----

.. class:: sipa.model.user.BaseUser
   :noindex:


`.fancy_property`
-----------------

..
  TODO use better documentation here!


.. automodule:: sipa.model.fancy_property
   :member-order: bysource
   :members:
   :undoc-members:
   :noindex:


`.finance`
----------

Related to the information the user returns, we demand the following form
of the finance information:

.. automodule:: sipa.model.finance
   :member-order: bysource
   :members:
   :private-members:
   :undoc-members:
   :noindex:
