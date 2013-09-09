# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010, 2degrees Limited <egoddard@tech.2degreesnetwork.com>.
# All Rights Reserved.
#
# This file is part of djangoaudit <https://launchpad.net/django-audit/>,
# which is subject to the provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Tests for djangoaudit"""
from datetime import datetime, timedelta, date
from decimal import Decimal
import os

# Have to set this here to ensure this is Django-like
os.environ['DJANGO_SETTINGS_MODULE'] =  "tests.fixtures.sampledjango.settings"

from django.conf import settings
from django.db.models import Sum
from nose.tools import (eq_, ok_, assert_false, assert_not_equal, assert_raises,
                        raises)
from pymongo.errors import PyMongoError
from fixture.django_testcase import FixtureTestCase


#from mongofixture import MongoFixtureTestCase
from djangoaudit.models import (_coerce_data_to_model_types, _audit_model, 
                                _coerce_to_bson_compatible, AuditedModel)
from djangoaudit.connection import MONGO_CONNECTION
from tests.fixtures.sampledjango.bsg.models import *
from tests.fixtures.sampledjango.bsg.fixtures import *


class TestEnsureBSONCompatible(object):
    """Test for :func:`_coerce_to_bson_compatible`"""
    
    def test_decimal_to_float(self):
        """Ensure that :class:`Decimal` is converted to :class:`float`"""
        
        got = _coerce_to_bson_compatible(Decimal('1234.5678'))
        expected = 1234.5678
        
        eq_(got, expected, 
            "Expected %r, got %r for Decimal to float conversion" % 
            (expected, got))
        
    def test_date_to_datetime(self):
        """Ensure that :class:`date` is converted to :class:`datetime`"""
        
        got = _coerce_to_bson_compatible(date(2001, 9, 11))
        expected = datetime(2001, 9, 11)
        
        eq_(got, expected, 
            "Expected %r, got %r for date to datetime conversion" % 
            (expected, got))


class MockModelMeta(object):
    """ Mock of :class:`django.db.options.Options` """
    
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.object_name = model_name


class MockModel(object):
    """ Mock of :class:`django.db.models.base.Model` """
    
    def __init__(self, app_label, model_name, pk):
        self._meta = MockModelMeta(app_label, model_name)
        self.pk = pk


class TestAuditModel(object):
    """ Tests for :func:`djangoaudit.models.audit_model` """
    
    
    def setup(self):
        self.audit_collection_name = "audit_data"
        self.auditing_collection = MONGO_CONNECTION\
            .get_collection(self.audit_collection_name)
        self.profile = MockModel("profiles", "Profile", 123)
                
    def fetch_record_by_id(self, id):
        
        return self.auditing_collection.find_one({"_id":id})
    
    def test_no_changes_empty_dicts(self):
        """Check that passing two empty value dicts results in a no-op"""
        result = _audit_model(self.profile, {}, {})
        
        eq_(result, None, "No changes should not result in anything being "
            "written to the database")
        
    def test_no_changes_same_values(self):
        """Check that passing two identical dicts results in a no-op"""
        
        result = _audit_model(self.profile,
                             {'foo': 1, 'bar': 'wibble', 'empty': None,
                               'my_date': datetime(2001, 1, 1, 9, 12)},
                             {'foo': 1, 'bar': 'wibble', 'empty': None,
                               'my_date': datetime(2001, 1, 1, 9, 12)})
        
        eq_(result, None, "No changes should not result in anything being "
            "written to the database")
        
    def test_single_change_no_other_diff(self):
        """Check that a single changed value is correctly recorded"""
        
        result = _audit_model(self.profile, dict(foo=None), dict(foo='bar'))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        eq_(saved_record['foo'], 'bar',
            "The saved record should contain a single difference key")
        
    def test_model_data_write_out(self):
        """Check the correct data is written out for the model"""
        
        result = _audit_model(self.profile, dict(foo=None), dict(foo='bar'))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        eq_(saved_record['object_app'], self.profile._meta.app_label)
        eq_(saved_record['object_model'], self.profile._meta.object_name)
        eq_(saved_record['object_pk'], self.profile.pk)
        
    def test_date_stamping(self):
        """Check that a date stamp is stored in along with the record"""
        
        result = _audit_model(self.profile, dict(foo=None), dict(foo='bar'))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        record_date_stamp = saved_record['audit_date_stamp']
        
        now = datetime.utcnow()
        
        ok_((now - timedelta(seconds=1)) < record_date_stamp < now,
            "Date stamp should be almost the same as now (now: %s, got: %s"
            % (now, record_date_stamp))
    
    def test_addition_parameter_write_out(self):
        """Check that additional parameters are correctly stored"""
        
        result = _audit_model(self.profile, dict(foo=None), dict(foo='bar'))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
    def test_single_change_others_same(self):
        """Check that a single changed value is correctly recorded when there are no other differences"""
        
        result = _audit_model(self.profile, dict(foo=None, wibble=0),
                             dict(foo='bar', wibble=0))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        eq_(saved_record['foo'], 'bar',
            "The saved record should contain a single difference key")
        
        ok_('wibble' not in saved_record, "There should be no "
            "record of changes to the `wibble` key")
        
    def test_multi_change_no_others(self):
        """Check that multiple changed values are correctly recorded when there are no other items"""
        
        result = _audit_model(self.profile, dict(foo=None, wibble=0),
                             dict(foo='bar', wibble=1))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        eq_(saved_record['foo'], 'bar',
            "The saved record should contain a difference for key `foo`")
        
        eq_(saved_record['wibble'], 1,
            "The saved record should contain a difference for key `wibble`")
        
    def test_multi_change_others_same(self):
        """Check that multiple changed values are correctly recorded when there are no other differences"""
        
        result = _audit_model(self.profile, dict(foo=None, wibble=0, body_count=1.00),
                             dict(foo='bar', wibble=1, body_count=1.00))
        
        assert_not_equal(result, None,
                         "A change should result in a database object being "
                         "created")
        
        saved_record = self.fetch_record_by_id(result)
        
        eq_(saved_record['foo'], 'bar',
            "The saved record should contain a difference for key `foo`")
        
        eq_(saved_record['wibble'], 1,
            "The saved record should contain a difference for key `wibble`")
        
        ok_('body_count' not in saved_record, "There should be no "
            "record of changes to the `body_count` key")
      

class TestCoerceDataToModelTypes(object):
    """Tests for :func:`_coerce_data_to_model_types`"""
    
    def setup(self):
        checks = (
            ('age', '40', 40),
            ('last_flight', date(2010, 1, 1), datetime(2010, 1, 1)),
            ('fastest_landing',71.10, Decimal("71.10")),
            ('is_cylon', 0, False),
        )
        
        self.initial_data, self.final_data = {}, {}
        
        for key, initial, final in checks:
            self.initial_data[key] = initial
            self.final_data[key] = final
    
    def test_for_instance(self):
        """Test _coerce_data_to_model_types for model instances"""
        
        pilot = Pilot()
        
        result = _coerce_data_to_model_types(pilot, self.initial_data)
        
        eq_(result, self.final_data, 
            "Expected to get: %r, got %r" % (result, self.final_data))
    
    def test_for_class(self):
        """Test _coerce_data_to_model_types for the model itself"""
        
        result = _coerce_data_to_model_types(Pilot, self.initial_data)
        
        eq_(result, self.final_data, 
            "Expected to get: %r, got %r" % (result, self.final_data))


class TestAuditedModel(FixtureTestCase):
    """Tests for AuditedModel"""
    
    datasets = [PilotData, VesselData]
    
    def setUp(self):
        self.audit_collection_name = "audit_data"
        
        self.auditing_collection = MONGO_CONNECTION\
            .get_collection(self.audit_collection_name)
            
        # Now set up the records:
        self.helo = Pilot.objects.filter(call_sign="Helo")[0] # wtf - no idea why fixture seems to be putting two of these in the DB
        self.athena = Pilot.objects.get(call_sign="Athena")
        self.starbuck = Pilot.objects.get(call_sign="Starbuck")
        self.apollo = Pilot.objects.get(call_sign="Apollo")
        self.longshot = Pilot.objects.get(call_sign="Longshot")
        self.raptor259 = Vessel.objects.get(name=VesselData.Raptor259.name)
        
    @raises(AttributeError)
    def test_meta_class(self):
        """Check that any values specified in log_fields which are no fields on the AuditedModel class cause an AttributeError to be raised"""
        
        class NaughtyAuditedModel(AuditedModel):
            log_fields = ['foo', 'bar', 'wibble']
            
    
    def test_no_changes_no_extra(self):
        """Check that when there are no changes to a AuditedModel instance, no changes are recorded"""
        
        # Set up the operator and some notes:
        self.helo.set_audit_info(operator='me',
                                 notes='This should not be recorded')
        
        # Save a model with no changes:
        self.helo.save()
        
        # Now read back the log to see whether anything was put in there:
        num_log_items = len(list(self.helo.get_audit_log()))
        eq_(num_log_items, 1, "There should be only be one log entry for this "
            "object - the creation log (found %d log entries)." % num_log_items)
        
    def test_change_non_logger_field(self):
        """Check that altering non-logged fields doesn't result in a log entry being generated"""
        
        self.helo.craft = 0
        
        # Set up the operator and some notes:
        self.helo.set_audit_info(operator='me',
                                 notes='This should not be recorded')
        self.helo.save()
        
        # Now read back the log to see whether anything was put in there:
        num_log_items = len(list(self.helo.get_audit_log()))
        
        eq_(num_log_items, 1, "There should be one log entry for this object - "
            "the creation log (found %d log entries)." % num_log_items)
        
    def test_create_fresh_record(self):
        """Check that creation of a record logs all the fields correctly"""
        
        self.athena.delete()
        
        params = dict(first_name="Sharon",
                      last_name="Agathon",
                      call_sign="Athena",
                      age=29,
                      last_flight=datetime(2000, 3, 4, 7, 18), 
                      craft=1,
                      is_cylon=True,
                      fastest_landing=Decimal("77.90"))
        
        new_athena = Pilot(**params)
        new_athena.save()
        
        log = list(new_athena.get_audit_log())
        
        # Check we've only got one log entry:
        eq_(len(log), 1, "There should only be one entry for this object (found"
            " %d)" % len(log))
        
        entry = log[0]
        
        # Now verify that we've only got the correct keys in the log, once we've
        # popped off the extra ones:
        object_app = entry.pop('object_app')
        object_model = entry.pop('object_model')
        object_pk = entry.pop('object_pk')
        id = entry.pop('_id')
        audit_date_stamp = entry.pop('audit_date_stamp')
        
        eq_(object_app, "bsg", 
            "object_app should be 'bsg', got %r" % object_app)                      
        eq_(object_model, "Pilot", 
            "object_model should be 'Pilot', got %r" % object_model)
        eq_(object_pk, new_athena.pk, "object_pk should be %r, got %r" % 
            (new_athena.pk, object_pk))
        
        # Our resulting entry should have only the audit_changes key as there is
        # only audited_data remaining:
        expected_keys = set(('audit_changes',))#set(new_athena.log_fields)
        found_keys = set(entry.keys())
        
        eq_(expected_keys, found_keys, "Mismatch between expected fields in the"
            " log. Expected %r, got %r" % (expected_keys, found_keys))
        
        # Now verify that what's on the new model is what was logged:
        for key, value in entry['audit_changes'].iteritems():
            expected = (None, getattr(new_athena, key))
            eq_(value, expected, "Expected to find %r with value: %r, got %r" %
                (key, expected, value))
    
    def test_partial_update(self):
        """Check that partial data updates are recorded correctly"""
        orig_name = self.longshot.last_name
        self.longshot.last_name = "New name"
        orig_age = self.longshot.age 
        self.longshot.age = 30
        orig_fastest_landing = self.longshot.fastest_landing 
        self.longshot.fastest_landing = Decimal("75.00")
        
        # Ensure we've got some operator testing too:
        operator, notes = "me", "This record should be updated"
        self.longshot.set_audit_info(operator=operator,notes=notes)
        
        # Now do the save:
        self.longshot.save()
        
        # Read back the log:
        log = list(self.longshot.get_audit_log())
        
        eq_(len(log), 2, "There should only be two entires for this object ("
            "found %d)" % len(log))
        
        entry = log[-1]
        
        # Now verify that we've only got the correct keys in the log, once we've
        # popped off the extra ones:
        object_app = entry.pop('object_app')
        object_model = entry.pop('object_model')
        object_pk = entry.pop('object_pk')
        id = entry.pop('_id')
        audit_date_stamp = entry.pop('audit_date_stamp')
        audit_operator = entry.pop('audit_operator')
        audit_notes = entry.pop('audit_notes')
        
        eq_(object_app, "bsg", 
            "object_app should be 'bsg', got %r" % object_app)                      
        eq_(object_model, "Pilot", 
            "object_model should be 'Pilot', got %r" % object_model)
        eq_(object_pk, self.longshot.pk, "object_pk should be %r, got %r" % 
            (self.longshot.pk, object_pk))
        eq_(audit_operator, operator, 
            "operator should be %r, got %r" % (operator, audit_operator))
        eq_(audit_notes, notes, 
            "notes should be %r, got %r" % (notes, audit_notes))
        
        # Check we've only got one key left (audit_changes):
        expected_keys = ['audit_changes']
        found_keys = entry.keys()
        eq_(expected_keys, found_keys, "Expected to find keys: %r, gor %r" %
            (expected_keys, found_keys))
        
        # Ensure that the new values were correctly recorded:
        changes= entry['audit_changes']
        eq_(changes['last_name'], (orig_name, self.longshot.last_name))
        eq_(changes['age'], (orig_age, self.longshot.age))
        eq_(changes['fastest_landing'], (orig_fastest_landing,
                                         self.longshot.fastest_landing))
                
    def test_dual_update(self):
        """Test that two log entries are generated for dual updates"""
        
        self.apollo.age = 40
        self.apollo.save()
        
        self.apollo.age = 30
        self.apollo.save()
        
        log = list(self.apollo.get_audit_log())
        
        eq_(len(log), 3, "There should be three entries in the log, got %d" %
            len(log))
        
        expected_ages = [(28, 40), (40, 30)]
        
        for entry, age in zip(log[1:], expected_ages):
            eq_(entry['audit_changes']['age'], age,
                "Expected age to be %r, got %r" % (entry['audit_changes']['age'], age))
    
    def test_delete(self):
        """Check that delete() records the final state of the model prior to deletion"""
        
        # Define the lookup key we'll need parameters to look up the record:
        pk = self.starbuck.pk
        
        self.starbuck.delete()
        
        # Delete another to make sure we don't get log cross-over:
        apollo_pk = self.apollo.pk
         
        self.apollo.set_audit_info(notes="Extra note")
        self.apollo.delete()
        
        # Get hold of the delete log:
        log = list(Pilot.get_deleted_log(pk))
        
        # Make sure there's only one entry:
        eq_(len(log), 1, 
            "There should only be one deleted item for this pk (found %d)" % 
            len(log))
        
        entry = log[0]
        
        for field in Pilot.log_fields:
            expected = getattr(PilotData.Starbuck, field)
            found = entry[field]
            
            eq_(expected, found, 
                "For field %r, expected %r, got %r" % (field, expected, found))
        
        delete_note = "Object deleted. These are the attributes at delete time."
        
        eq_(entry['audit_notes'], delete_note, 
            "Expected to find notes as: %r, got %r" % 
            (delete_note, entry['audit_notes']))
        
        # Get hold of the delete log for apollo to check the delete note:
        entry = list(Pilot.get_deleted_log(apollo_pk))[0]
        got = entry['audit_notes']
        expected = "%s\nExtra note" % delete_note
        
        eq_(expected, got, "Expected note: %r, got %r" % (expected, got))
        
        # Since we've deleted two items we can check that we've got the log for
        # both of these:
        log = list(Pilot.get_deleted_log())
        
        eq_(len(log), 2, 
            "There should be two deleted log entries for this class (found %d)"
            % len(log))
    
    def test_arbitrary_audit(self):
        """Test the arbitrary auditing of data against a model"""
        
        data = dict(hair_colour="Blond",
                    children=0,
                    kill_percentage=Decimal('98.7'))
        
        self.starbuck.set_audit_info(**data)
        self.starbuck.save()
        
        log = list(self.starbuck.get_audit_log())
        
        eq_(len(log), 2, 
            "There should only be two entries in the log (found %d)" % len(log))
        
        entry = log[-1]
        object_app = entry.pop('object_app')
        object_model = entry.pop('object_model')
        object_pk = entry.pop('object_pk')
        id = entry.pop('_id')
        audit_date_stamp = entry.pop('audit_date_stamp')
        
        eq_(object_app, "bsg", 
            "object_app should be 'bsg', got %r" % object_app)                      
        eq_(object_model, "Pilot", 
            "object_model should be 'Pilot', got %r" % object_model)
        eq_(object_pk, self.starbuck.pk, "object_pk should be %r, got %r" % 
            (self.starbuck.pk, object_pk))
        
        # Mongo stores Decimals as floats, so coerce what we expect:
        data['kill_percentage'] = float(data['kill_percentage'])
        
        eq_(entry, data, "Expecting %r, got %r" % (data, entry))
        
    def test_foreign_keys(self):
        """Test the foreign keyed fields don't interfere with AuditedModel"""
        
        # Due to a call in the metaclass of AuditedModel, the
        # _meta.get_all_field_names does not behave correctly unless the cache
        # is cleared after this call. Aggregation is one area where this 
        # manifests itself - here we're ensuring this doesn't fail:
        field_names = Pilot._meta.get_all_field_names()
        
        ok_("vessels" in field_names,
            "The field names for the Pilot model should contain 'vessels', got "
            "%s" % field_names)
                
        # Now verify in aggregation this works:
        vessel_sum = Pilot.objects.aggregate(Sum('vessels'))['vessels__sum']
        
        eq_(vessel_sum, 1, "There should only be one vessel, got %r" 
            % vessel_sum)
        
    def test_get_creation_log(self):
        """Test that the creation log can be retrieved correctly"""
        
        # Create a new object:
        hot_dog = Pilot(
            first_name="Brendan",
            last_name="Costanza",
            call_sign="Hot Dog",
            age=25,
            last_flight=datetime(2000, 6, 4, 23, 01), 
            craft=1,
            is_cylon=False,
            fastest_landing=Decimal("101.67")
        )
        
        hot_dog.set_audit_info(operator="Admin",
                               flight_deck="Port side")
        
        hot_dog.save()
        
        # Retrieve the log as a check:
        initial_log = hot_dog.get_creation_log()
        
        # Make another entry:
        hot_dog.fastest_landing = Decimal("99.98")
        hot_dog.save()
        
        # Check we've got two items in the log now:
        found_logs = len(list(hot_dog.get_audit_log()))
        eq_(2, found_logs, "Expected to find 2 logs, got %d" % found_logs)
        
        # Now check the creation log:
        creation_log = hot_dog.get_creation_log()
        eq_(creation_log, initial_log, "Expecting initial log entry to be the "
            "same as the creation log. Expected:\n%r,\n\ngot\n%r" %
             (initial_log, creation_log))
        
        # Test that fail gracefully when no creation log exists:
        for item in hot_dog.get_audit_log():
            self.auditing_collection.remove(item['_id'])
        
        empty_log = hot_dog.get_creation_log()
        
        eq_(empty_log, None, "The creation log should be None")
        
    def test_get_deletion_log(self):
        """Test that deleted data can be retrieved"""
        
        pre_delete_data = {}
        for field in self.apollo.log_fields:
            pre_delete_data[field] = getattr(self.apollo, field)
            
        pk = self.apollo.pk
        
        self.apollo.delete()
        
        # Get the deletion log:
        entry = list(Pilot.get_deleted_log(pk))[0]
             
        object_app = entry.pop('object_app')
        object_model = entry.pop('object_model')
        object_pk = entry.pop('object_pk')
        id = entry.pop('_id')
        audit_date_stamp = entry.pop('audit_date_stamp')
        audit_is_delete = entry.pop('audit_is_delete')
        audit_notes = entry.pop('audit_notes')
        
        ok_(audit_is_delete, "Should have audit_is_delete is True")
        eq_(audit_notes,
            'Object deleted. These are the attributes at delete time.')
        
        
        eq_(pre_delete_data, entry,
            "Expected to find deletion log as: %r, got %r" % 
            (pre_delete_data, entry))