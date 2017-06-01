#!/usr/bin/env python
# * coding: utf8 *
'''
stats.py

A module that contains
'''

import arcpy
from .command import Command
from boost.config import feature_classes


class Stats(Command):

    def execute(self):
        self.validate(self.options)

        #: define workspace geodatabse
        arcpy.env.workspace = self.options['<workspace>']
        arcpy.env.overwriteOutput = True

        self.max_speeds(feature_classes['address_service_final'])
        self.address_counts(feature_classes['msba'], feature_classes['address_count_area'], feature_classes['address_count_type'],
                            feature_classes['address_count_county'])
        self.speed_tiers(feature_classes['msba'])
        self.speed_counts(feature_classes['msba'], feature_classes['counties'])

    def validate(self, options):
        if not self.options['--workspace']:
            raise Exception('--workspace needs to be set so we now what geodatabase to act on')

        if not arcpy.Exists(self.options['<workspace>']):
            raise Exception('We could not find {}. Will you make sure it exist and try again?'.format(self.options['<workspace>']))

    def max_speeds(self, address_points):
        '''find maximum download and upload speed for each address ( ~ 10 Minutes)
        '''
        print('Calculating Maximum Upload and Download Speeds for Addresses...')
        try:
            arcpy.Statistics_analysis(address_points, feature_classes['msba'], [['MaxDown', 'MAX'], ['MaxUp', 'MAX']], 'FID_AddressPoints')
        except:
            print(arcpy.GetMessages())
        try:
            #: calls function above. Adds new Max statistics back to main data table (~ 5 minutes)
            self.join_tables(feature_classes['msba'], address_points)
        except:
            print(arcpy.GetMessages())

    def address_counts(self, layer, out_name, out_type, out_county):
        '''find number of address points in each area by name.
        A new field 'Name_Area' is specified due to duplicate names (Emery=County and Emery=Municipality) This is
        important when running query script'''
        print('Calculating Address Count By Area Name...')
        try:
            arcpy.AddField_management(layer, 'Name_Area', 'Text')
            with arcpy.da.UpdateCursor(layer, ['Name_Area', 'NAME', 'AREA_TYPE']) as cursor:
                for row in cursor:
                    row[0] = '{}|{}'.format(row[1], row[2])
                    cursor.updateRow(row)

            arcpy.Statistics_analysis(layer, out_name, [['FID_AddressPoints', 'Count']], ['Name_Area'])
        except:
            print(arcpy.GetMessages())
        #: find number of address points in each area by area type (Municipality, Unincorporated, Other)
        print('Calculating Address Count By Area Type...')
        try:
            arcpy.Statistics_analysis(layer, out_type, [['FID_AddressPoints', 'Count']], ['AREA_TYPE'])
        except:
            print(arcpy.GetMessages())
        #: find number of address points in each area by County
        #: The 'other' category only represents County area that is not a municipality or unincorporated.
        #: This step gets an address count using the entire County's area
        print('Calculating Address Count By County...')
        try:
            arcpy.Statistics_analysis(layer, out_county, [['FID_AddressPoints', 'Count']], ['COUNTYNBR'])
        except:
            print(arcpy.GetMessages())

    def speed_tiers(self, table):
        '''Calculates Speed Tiers for MaxDown and MaxUp Speeds
        ~ 5 Minutes'''
        print('Calculating Speed Tiers...')
        arcpy.AddField_management(table, 'MaxDown_Tier', 'Short')
        arcpy.AddField_management(table, 'MaxUp_Tier', 'Short')

        #: TODO combine these to one loop
        with arcpy.da.UpdateCursor(table, ['MAX_MaxDown', 'MaxDown_Tier']) as cursor:
            for row in cursor:
                if row[0] < 0.768:
                    row[1] = 0
                elif 0.768 <= row[0] < 1.5:
                    row[1] = 3
                elif 1.5 <= row[0] < 3:
                    row[1] = 4
                elif 3 <= row[0] < 6:
                    row[1] = 5
                elif 6 <= row[0] < 10:
                    row[1] = 6
                elif 10 <= row[0] < 25:
                    row[1] = 7
                elif 25 <= row[0] < 50:
                    row[1] = 8
                elif 50 <= row[0] < 100:
                    row[1] = 9
                elif 100 <= row[0] < 1000:
                    row[1] = 10
                elif row[0] >= 1000:
                    row[1] = 11

                cursor.updateRow(row)
        with arcpy.da.UpdateCursor(table, ['MAX_MaxUp', 'MaxUp_Tier']) as cursor:
            for row in cursor:
                if row[0] < 0.768:
                    row[1] = 0
                elif 0.768 <= row[0] < 1.5:
                    row[1] = 3
                elif 1.5 <= row[0] < 3:
                    row[1] = 4
                elif 3 <= row[0] < 6:
                    row[1] = 5
                elif 6 <= row[0] < 10:
                    row[1] = 6
                elif 10 <= row[0] < 25:
                    row[1] = 7
                elif 25 <= row[0] < 50:
                    row[1] = 8
                elif 50 <= row[0] < 100:
                    row[1] = 9
                elif 100 <= row[0] < 1000:
                    row[1] = 10
                elif row[0] >= 1000:
                    row[1] = 11

                cursor.updateRow(row)

    def speed_counts(self, msba, counties):
        '''Calculates number of address points in each speed tier for: Counties
        '''
        print('Calculating Speed Tier Statistics for Counties...')
        arcpy.Frequency_analysis(msba, 'MaxDown_County', ['MaxDown_Tier', 'COUNTYNBR'])
        arcpy.Frequency_analysis(msba, 'MaxUp_County', ['MaxUp_Tier', 'COUNTYNBR'])
        tables = ['MaxDown_County', 'MaxUp_County']

        for table in tables:
            arcpy.JoinField_management(table, 'COUNTYNBR', counties, 'COUNTYNBR', ['NAME'])
            arcpy.JoinField_management(table, 'COUNTYNBR', feature_classes['address_count_county'], 'COUNTYNBR', ['COUNT_FID_AddressPoints'])

        #: Named Areas (Municipalities, Unincorporated, Other)
        print('Calculating Speed Tier Statistics for Areas...')
        arcpy.Frequency_analysis(msba, 'MaxDown_Area', ['MaxDown_Tier', 'Name_Area'])
        arcpy.Frequency_analysis(msba, 'MaxUp_Area', ['MaxUp_Tier', 'Name_Area'])

    def join_tables(self, target, join):
        '''join area data (area name, type, county) to MSBA statistics generated above
        this custom join function is much faster than the JoinField tool'''
        fieldlist = ['FID_AddressPoints', 'NAME', 'AREA_TYPE', 'COUNTYNBR']

        #: Step 1: Create dictionary of fields and values to be joined
        joindict = {}
        with arcpy.da.SearchCursor(join, fieldlist) as rows:
            for row in rows:
                joinval = row[0]
                val1 = row[1]
                val2 = row[2]
                val3 = row[3]
                joindict[joinval] = [val1, val2, val3]

        arcpy.AddField_management(target, 'NAME', 'TEXT')
        arcpy.AddField_management(target, 'AREA_TYPE', 'TEXT')
        arcpy.AddField_management(target, 'COUNTYNBR', 'TEXT')

        #:  Step 2: Specify Key Value field. If it exists in target, populate new fields with appropriate values
        with arcpy.da.UpdateCursor(target, fieldlist) as recs:
            for rec in recs:
                #: import pdb; pdb.set_trace()
                keyval = rec[0]
                if keyval in joindict:
                    rec[1] = joindict[keyval][0]
                    rec[2] = joindict[keyval][1]
                    rec[3] = joindict[keyval][2]

                recs.updateRow(rec)
