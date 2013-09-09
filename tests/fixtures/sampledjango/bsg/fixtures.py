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

"""Fixtures for Django DB related tests for AuditedModel"""

from datetime import datetime
from decimal import Decimal

from fixture import DataSet

__all__ = ['PilotData', 'VesselData']

class PilotData(DataSet):
    """Pilot fixtures for testing AuditedModel"""
    
    class Meta:
        django_model = "bsg.Pilot"
        
    class Helo:
        first_name = "Karl"
        last_name = "Agathon"
        call_sign = "Helo"
        age = 32
        last_flight = datetime(2000, 3, 4, 7, 18) 
        craft = 1
        is_cylon = False
        fastest_landing = Decimal("100.45")
        
    class Athena:
        first_name = "Sharon"
        last_name = "Agathon"
        call_sign = "Athena"
        age = 29
        last_flight = datetime(2000, 3, 4, 7, 18) 
        craft = 1
        is_cylon = True
        fastest_landing = Decimal("77.90")
        
    class Starbuck:
        first_name = "Kara"
        last_name = "Thrace"
        call_sign = "Starbuck"
        age = 27
        last_flight = datetime(2000, 2, 4, 5, 59) 
        craft = 0
        is_cylon = False
        fastest_landing = Decimal("46.77")
        
    class Apollo:
        first_name = "Lee"
        last_name = "Adama"
        call_sign = "Apollo"
        age = 28
        last_flight = datetime(1999, 12, 20, 17, 56) 
        craft = 0
        is_cylon = False
        fastest_landing = Decimal("71.10")
        
    class Longshot:
        first_name = "Samuel"
        last_name = "Anders"
        call_sign = "Longshot"
        age = 25
        last_flight = datetime(2000, 5, 1, 1, 38) 
        craft = 0
        is_cylon = True
        fastest_landing = Decimal("79.99")
        
class VesselData(DataSet):
    """Pilot fixtures for testing AuditedModel"""
    
    class Meta:
        django_model = "bsg.Vessel"
        
    class Raptor259:
        name = "Raptor 259"
        pilot = PilotData.Athena
        