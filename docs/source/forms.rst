==================
Working with forms
==================

.. module:: djangoaudit.forms

.. topic:: Overview

	Since ModelForm performs an implicit :meth:`save` on the underlying model
	when its :meth:`save` is called, you won't necessarily have the chance to
	record the operator and notes on the form instance. For convenience in this
	situation :class:`AuditedModelForm` is provided
	
AuditedModelForm
================

The only thing that you will need to consider with audited model forms is that
:meth:`~AuditedModelForm.save` takes two optional keyword arguments: 
``operator`` and ``notes``. These work the same as in 
:meth:`djangoaudit.models.AuditedModel.set_audit_info`.

API Documentation
=================

.. autoclass:: AuditedModelForm
	:members:
	
