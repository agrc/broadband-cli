#!/usr/bin/env python
# * coding: utf8 *
'''
config.py

A module that contains the static names and places of feature classes
'''

feature_classes = {
    #: Input dataset names, set these (must all exist in the workspace gdb)
    #: Current Broadband Service layer
    'bb_service': 'Utilities_BroadbandService_20200930',
    #: Current Address Points layer
    'address_points': 'AddressPoints_20200923',
    #: County Boundaries
    'counties': 'county_boundaries',
    #: Municipal Boundaries
    'municip': 'municipal_boundaries',
    #: Approximate unincorporated areas
    'unincorp': 'unincorporated_boundaries',

    #: Output dataset names
    'address_service_final': 'Address_Service_Final',
    'msba': 'MSBA',
    'address_count_area': 'AddressCount_AreaName',
    'address_count_type': 'AddressCount_AreaType',
    'address_count_county': 'AddressCount_County'
}
