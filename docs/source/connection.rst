=========================
The connection to MongoDB
=========================

.. topic:: Overview
	
	The connection module is not intended to be part of the public API for
	django-audit, but you may find it helpful if you want to perform some custom
	work on the auditing collection as such just the `API documentation`_ is
	included here.
	
API Documentation
=================

.. module:: djangoaudit.connection

.. autoclass:: MongoConnection
	:members:
	
.. data:: MONGO_CONNECTION
	
	This module level variable should be the only thing that is imported as it
	sets up the connection to MongoDB based on the django settings.