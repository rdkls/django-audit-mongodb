==============
Audited Models
==============

.. module:: djangoaudit.models

.. topic:: Overview

	django-audit provides a single class :class:`AuditedModel` which
	is a subclass of :class:`django.db.models.Model` to handle the auditing for
	you. The only thing you'll need to define is which fields to log and the
	rest is taken care for you!
	
Creating your model
===================

To get started with auditing your model, you'll need to subclass
:class:`AuditedModel` and define the :attr:`log_fields` attribute,
e.g.::

	from django.db import models
	
	from djangoaudit.models import AuditedModel
	
	class Pilot(AuditedModel):
	    """A dummy model to test the functionality of the AuditedModel"""
	    
	    log_fields = ('first_name', 'last_name', 'call_sign', 'age', 'last_flight',
	                  'is_cylon', 'fastest_landing')
	    
	    first_name = models.CharField(max_length=30)
	    last_name = models.CharField(max_length=30)
	    call_sign = models.CharField(max_length=30)
	    age = models.IntegerField()
	    last_flight = models.DateTimeField(null=True, blank=True)
	    craft = models.IntegerField(choices=CRAFT_CHOICES)
	    is_cylon = models.BooleanField(default=False)
	    fastest_landing = models.DecimalField(max_digits=5, decimal_places=2)
	    
	    def __unicode__(self):
	        return self.call_sign
	        
:attr:`log_fields` can be any sequence provided the values are all names of the
fields you have declared on your models.

.. warning:: 
	
	If you specify a field which is not declared on the models a :exc:`ValueError`
	will be raised when you start your application.
	
In the example above we want to log most of the fields on the :class:`Pilot`
model. When new instances of :class:`Pilot` are created, modified or deleted,
the changes to these fields will be recorded.

Auditing data
=============

Auditing happens at the following times:

* `Model creation`_
* `Model modification`_ (saving)
* `Model deletion`_
* `Recording extra information`_

Model creation
--------------

When you create an instance of your model and save it for the first time the
initial values of all the :attr:`log_fields` will be recorded::

	>>> from datetime import datetime
	>>> from decimal import Decimal
	>>> hot_dog = Pilot(
	            first_name="Brendan",
	            last_name="Costanza",
	            call_sign="Hot Dog",
	            age=25,
	            last_flight=datetime(2000, 6, 4, 23, 01), 
	            craft=1,
	            is_cylon=False,
	            fastest_landing=Decimal("101.67")
	        )
	>>> hot_dog.save()   
	>>> hot_dog.get_creation_log()
	{u'fastest_landing': Decimal("101.67"), u'last_flight': datetime.datetime(2000, 6, 4, 23, 1), u'last_name': u'Costanza', u'object_pk': 340, u'call_sign': u'Hot Dog', u'first_name': u'Brendan', u'is_cylon': False, u'_id': ObjectId('4c0f8e8b38b72a6f97000000'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 12, 52, 27, 717000), u'object_app': u'bsg', u'object_model': u'Pilot', u'age': 25}
	
For more information on retrieving the creation log, see `retrieving the 
creation log`_.

We see that when we read back the log entry for creation all the fields
specified in :attr:`log_fields` appear in the returned dictionary as well as
some identifiers that relate the data to the particular model instance and the
ObjectId from the MongoDB collection.

Model modification
------------------

When you make any changes to a model and called the save method the delta of the
values will be recorded. That is to say only those fields in :attr:`log_fields`
which have changed since the model was last saved will be logged.

.. warning::
	Only the :meth:`~AuditedModel.save` will trigger the auditing. If you call
	:meth:`update` on a queryset, the save method won't be triggered and no data
	will be audited.
	
	However, any process which implicitly trigger :meth:`~AuditedModel.save`
	will cause the changes to be recorded.
	
We can see this in process by picking up where we left off above. First if we
change the :attr:`age` we see this in the last log entry::

	>>> hot_dog.age = 26
	>>> hot_dog.save()
	>>> list(hot_dog.get_audit_log())[-1]
	{u'object_app': u'bsg', 'audit_changes': {u'age': (25, 26)}, u'object_pk': 340, u'_id': ObjectId('4c0f91d038b72a6f97000001'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 13, 6, 24, 557000), u'object_model': u'Pilot'}
	
This time the age is returned as a :class:`tuple` of the value before the change
and the value after. (For more information on retrieving the audit log, see
`retrieving the audit log`_).

Conversely if we change :attr:`craft` and save, no changes will be recorded as
:attr:`craft` is not one of the log fields::

	>>> hot_dog.craft = 45
	>>> hot_dog.save()
	>>> list(hot_dog.get_audit_log())[-1]
	{u'object_app': u'bsg', 'audit_changes': {u'age': (25, 26)}, u'object_pk': 340, u'_id': ObjectId('4c0f91d038b72a6f97000001'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 13, 6, 24, 557000), u'object_model': u'Pilot'}

In this case, when we retrieve the last log entry, we see that we have the log
for the previous change with no mention of the craft.

If we want to change the age back to its original value, we can do this::

	>>> hot_dog.age = 25
	>>> hot_dog.save()
	>>> list(hot_dog.get_audit_log())[-1]
	{u'object_app': u'bsg', 'audit_changes': {u'age': (26, 25)}, u'object_pk': 340, u'_id': ObjectId('4c0f931638b72a6f97000002'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 13, 11, 50, 17000), u'object_model': u'Pilot'}

The reversal of the age in now recorded.

Model deletion
--------------

When we delete a model instance from the database, we want to know how it looked
just before it was deleted. We can access information for a specific model or
for a particular instance (see `retrieving the deletion log`_)::

	>>> pk = hot_dog.pk
	>>> hot_dog.delete()
	>>> list(Pilot.get_deleted_log(pk))
	[{u'fastest_landing': Decimal("101.67"), u'last_flight': datetime.datetime(2000, 6, 4, 23, 1), u'last_name': u'Costanza', u'age': 25, u'call_sign': u'Hot Dog', u'first_name': u'Brendan', u'is_cylon': False, u'_id': ObjectId('4c0f93a538b72a6f97000003'), u'audit_is_delete': True, u'audit_notes': u'Object deleted. These are the attributes at delete time.', u'audit_date_stamp': datetime.datetime(2010, 6, 9, 13, 14, 13, 313000), u'object_app': u'bsg', u'object_model': u'Pilot', u'object_pk': 340}]
	
Here, we see that the log contains a single item (as only one object was 
deleted) containing all the last known values for the object.

Recording extra information
---------------------------

If you need to record extra information with a change to the model, AuditedModel
provides :meth:`~AuditedModel.set_audit_info`. This method accepts any keyword
arguments and will log these as such. The keys can be other fields from the
model or simply anything else you wish to record.

The audit process does support two special keys in :meth:`~AuditedModel.set_audit_info`:

* Operator
* Notes

These are designed so that they will always avoid a name clash with any fields
on the models and in the log will be prefixed with *audit_*. For most uses these
should be sufficient for recording any extra information, but you may also wish
to provide other data. Any other data will not be prefixed::

	>>> hot_dog.set_audit_info(operator="Someone", notes="Quick update", hyperspace=True)
	>>> hot_dog.save()
	>>> list(hot_dog.get_audit_log())[-1]['operator']
	------------------------------------------------------------
	Traceback (most recent call last):
	  File "<ipython console>", line 1, in <module>
	KeyError: 'operator'
	
	>>> list(hot_dog.get_audit_log())[-1]['audit_operator']
	u'Someone'
	>>> list(hot_dog.get_audit_log())[-1]['audit_notes']
	u'Quick update'
	>>> list(hot_dog.get_audit_log())[-1]['hyperspace']
	True	

Reading from the logs
=====================

There are three sets of logs read-back options available:

* `Retrieving the creation log`_ (:meth:`~AuditedModel.get_creation_log`)
* `Retrieving the audit log`_ (:meth:`~AuditedModel.get_audit_log`)
* `Retrieving the deletion log`_ (:meth:`~AuditedModel.get_deleted_log`)

Retrieving the creation log
---------------------------

To get the creation log for your audited model,
:meth:`~AuditedModel.get_creation_log` on the model instance::

	>>> hot_dog.get_creation_log()
	{u'fastest_landing': Decimal("101.67"), u'last_flight': datetime.datetime(2000, 6, 4, 23, 1), u'last_name': u'Costanza', u'object_pk': 340, u'call_sign': u'Hot Dog', u'first_name': u'Brendan', u'is_cylon': False, u'_id': ObjectId('4c0f8e8b38b72a6f97000000'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 12, 52, 27, 717000), u'object_app': u'bsg', u'object_model': u'Pilot', u'age': 25}
	
This will return a dictionary of all the values at creation time of the model. 

Retrieving the audit log
------------------------

To see all the entries over the history of the audited model instance call
:meth:`~AuditedModel.get_audit_log`. This will return a generator that you can
iterate over::

	>>> hot_dog.get_audit_log()
	<generator object at 0x949a2ec>
	>>> for entry in hot_dog.get_audit_log():
	...     print entry['audit_changes']
	...     
	{u'fastest_landing': (None, Decimal("101.67")), u'last_flight': (None, datetime.datetime(2000, 6, 4, 23, 1)), u'last_name': (None, u'Costanza'), u'age': (None, 25), u'first_name': (None, u'Brendan'), u'is_cylon': (None, False), u'call_sign': (None, u'Hot Dog')}
	{u'age': (25, 26)}
	{u'age': (26, 25)}
	{u'last_name': (u'Costanza', u'New last name')}
	
In this case a dictionary will be available with the key ``audit_changes``,
which contains a tuple for each logged field that has been changed to indicate
the *before* and *after* value.

For the first entry (the creation), the *before* value will always be ``None``.

For all fields which are not specified in :attr:`log_fields`, the value in the
log at the time will reported. We can see this if we log the operator with
another save::

	>>> hot_dog.first_name = "New first name"
	>>> hot_dog.set_audit_info(operator="Me")
	>>> hot_dog.save()
	>>> list(hot_dog.get_audit_log())[-1]
	{u'object_model': u'Pilot', 'audit_changes': {u'first_name': (u'Brendan', u'New first name')}, u'object_pk': 340, u'audit_operator': u'Me', u'_id': ObjectId('4c0faa0b38b72a6f97000006'), u'audit_date_stamp': datetime.datetime(2010, 6, 9, 14, 49, 47, 140000), u'object_app': u'bsg'}
	>>> list(hot_dog.get_audit_log())[-1]['audit_operator']
	u'Me'
	>>> list(hot_dog.get_audit_log())[-1]['audit_changes']
	{u'first_name': (u'Brendan', u'New first name')}

For an explanation of logging extra information with a change, see `recording
extra information`_.

.. note::
	
	In the case of :meth:`~AuditedModel.get_audit_log`, the first entry (i.e.
	the creation log) is not reported in the same manner as in 
	:meth:`~AuditedModel.get_creation_log`.

Retrieving the deletion log
---------------------------

Once an audited model instance has been deleted, it may be desirable to view the
object at the time of deletion. To facilitate this there is a class method 
provided on AuditedModel subclasses: :meth:`~AuditedModel.get_deleted_log`.

If this is called with no arguments, all logs for this model will be retrieved.
If a primary key is specified as the argument, only the deletion logs for that
object will be retrieved.

.. note::
	
	This class method is a generator so you will need to iterate over it to 
	retrieve the logs.

API Documentation
=================

.. autoclass:: AuditedModel
	:members:

