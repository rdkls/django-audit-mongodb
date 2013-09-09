===============
Getting started
===============

.. topic:: Overview

	django-audit should plug right alongside django, but you will need to get
	an instance of MongoDB set-up for recording the data.
	
Installing MongoDB
==================

The most reliable way to install MongoDB is to use a package if you are running
an OS that supports these. See http://www.mongodb.org/display/DOCS/Downloads#Downloads-Packages
for instructions.

If there isn't a package available, follow the `quick start instructions
<http://www.mongodb.org/display/DOCS/Quickstart>`_ to get up and running.

Installing django-audit
=======================

The easiest way to install django-audit is from `Pypi
<http://pypi.python.org/pypi/django-audit/>`_ via ``easy_install``:

.. code-block:: bash

	$ sudo easy_install django-audit
	
If you'd rather download the source, you can checkout the bazaar branch and then
run ``setup.py``:

.. code-block:: bash

	$ bzr branch lp:django-audit
	$ cd /path/to/checkout/
	$ sudo python setup.py install

Configuring your django application
===================================

django-audit requires a few settings to be defined in your django settings file.
These are:

* ``MONGO_HOST``
* ``MONGO_PORT``
* ``MONGO_DATABASE_NAME``

So a sample snippet from a ``settings.py`` file might look like::

	# Settings related to django-audit
	MONGO_HOST = 'localhost'
	MONGO_PORT = 27017
	MONGO_DATABASE_NAME = 'auditing'
	
What next?
==========

All that remains for you to do is to declared some AuditedModels or convert your
existing ones. For the model reference see :doc:`models`.
	
