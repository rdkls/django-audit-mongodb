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

"""
All Models which are only loaded for testing should be placed here. This is not
an INSTALLED_APP by default - the test config adds it.

"""
import os
print os.environ.get('DJANGO_SETTINGS_MODULE')
from django.db import models

from djangoaudit.models import AuditedModel

__all__ = ['Pilot', 'Vessel']

CRAFT_CHOICES = (
    (0, "Viper"),
    (1, "Raptor"),
)

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
    
class Vessel(AuditedModel):
    """A dummy model to test related fields"""
    
    log_fields = ['name']
    
    name = models.CharField(max_length=30)
    pilot = models.ForeignKey(Pilot, related_name="vessels")
    
    def __unicode__(self):
        return self.name