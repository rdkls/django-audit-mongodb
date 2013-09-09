django-audit-mongodb
====================

Audit Django model changes in MongoDB.

This is a mirror of Euan Goddard's repo on Launchpad here: https://launchpad.net/django-audit

with one change (/kludge) - cast all fields to strings when sending BSON to mongo.
Otherwise, for fk & m2m fields pymongo don't know how to serialize related Django models. And he die.
