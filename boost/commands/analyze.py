#!/usr/bin/env python
# * coding: utf8 *
'''
process.py
For use with ArcPro 1.4 and Python 3.5

This script calculates maximum upload and download speeds for each address, and the number of addresses in different
administrative boundaries. Broadband data is associated with address points using a Pairwise Intersect tool and an
Identity tool.

Two functions Analysis() and Statistics() are called that nest all the other functions. The output tables from
Statistics() can be used in the 'BBStats_query' script for further statistics.

Total runtime varies between 2-4 hours
'''

import arcpy
from arcpy.conversion import FeatureClassToFeatureClass
from .command import Command
from boost.config import feature_classes


class Analyze(Command):

    def execute(self):
        self.validate(self.options)

        #: define workspace geodatabse
        workspace = arcpy.env.workspace = self.options['<workspace>']
        arcpy.env.overwriteOutput = True

        analysis_fc = self.analysis_areas(feature_classes['counties'], feature_classes['municip'], feature_classes['unincorp'])
        dissolved_fc = self.composite_key(feature_classes['bb_service'])
        pairwise = self.pairwise_intersect([dissolved_fc, analysis_fc])
        self.identity(feature_classes['address_points'], pairwise, feature_classes['address_service_final'])
        self.add_keys(feature_classes['address_service_final'])
        self.populate_keys(feature_classes['address_service_final'])
        self.no_service(feature_classes['address_service_final'], analysis_fc, workspace)

    def validate(self, options):
        if not self.options['--workspace']:
            raise Exception('--workspace needs to be set so we now what geodatabase to act on')

        if not arcpy.Exists(self.options['<workspace>']):
            raise Exception('We could not find {}. Will you make sure it exist and try again?'.format(self.options['<workspace>']))

    def analysis_areas(self, counties, municip, unincorp):
        '''create area types for analysis
        '''
        layer = 'Analysis_Areas'
        print('Creating {} Layer...'.format(layer))
        try:
            arcpy.Union_analysis([municip, unincorp], 'Not_Counties')
            arcpy.Erase_analysis(unincorp, municip, 'Unincorporated')  #: Unincorporated
            arcpy.Erase_analysis(counties, 'Not_Counties', 'Other')  #: Counties
            arcpy.Delete_management('Not_Counties')
            #: redefine variables with new data
            other = 'Other'
            unincorp = 'Unincorporated'

            #: add new field 'Type' to each area category and populate with type name
            arcpy.AddField_management(other, 'Area_Type', 'TEXT')
            with arcpy.da.UpdateCursor(other, 'Area_Type') as cursor:
                for row in cursor:
                    row[0] = 'Other'
                    cursor.updateRow(row)

            arcpy.AddField_management(municip, 'Area_Type', 'TEXT')
            with arcpy.da.UpdateCursor(municip, 'Area_Type') as cursor:
                for row in cursor:
                    row[0] = 'Municipality'
                    cursor.updateRow(row)

            arcpy.AddField_management(unincorp, 'Area_Type', 'TEXT')
            with arcpy.da.UpdateCursor(unincorp, 'Area_Type') as cursor:
                for row in cursor:
                    row[0] = 'Unincorporated'
                    cursor.updateRow(row)

            #: Create 'Analysis_Areas' feature class
            #: Name field must be the same across all three feature classes
            arcpy.AlterField_management(unincorp, 'PLACENAME', 'NAME')

            #: Append counties and municipalities to Analysis_Areas
            #: (unincorp features)
            arcpy.Append_management([other, municip], unincorp, 'NO_TEST')

            #: Rename Unincorp to Analysis_Areas
            #: Note: This if/else seems redundant with overwriteOutput = True, but
            #: there were bugs regardless.
            #: This chunk took care of whatever was wrong
            if arcpy.Exists(layer):
                arcpy.Delete_management(layer)
                arcpy.Rename_management(unincorp, layer)
            else:
                arcpy.Rename_management(unincorp, layer)

            arcpy.Delete_management('Other')

            return layer
        except:
            print(arcpy.GetMessages())

    def composite_key(self, bb_service):
        '''create composite key values in BB_Service
        '''
        expression = '!UTProvCode! + "|" + str(!TRANSTECH!) + "|" + str(!MAXADDOWN!) + "|" + str(!MAXADUP!)'
        layer = 'BB_Service_Dissolve'

        print('Creating Composite Key in {}...'.format(layer))
        try:
            arcpy.AddField_management(bb_service, 'Key', 'TEXT', 70)
            arcpy.CalculateField_management(bb_service, 'Key', expression, 'PYTHON_9.3')
            #: Dissolve features based on the composite key
            arcpy.Dissolve_management(bb_service, layer, 'Key')

            return layer
        except:
            print(arcpy.GetMessages())

    def pairwise_intersect(self, fcs):
        '''intersects BB service areas against Analysis areas, creating unique polygons in BB_Service_Dissolve
        for each type in Analysis_Areas'''
        layer = 'BB_Service_Dissolve_Pairwise'

        print('Running Pairwise Intersection Tool creating {}...'.format(layer))
        try:
            arcpy.PairwiseIntersect_analysis(fcs, layer)

            return layer
        except:
            print(arcpy.GetMessages())

    def identity(self, identity_on, identity_features, output):
        '''attaches composite key values to AddressPoints based on their relationships to BB Service areas
        '''
        print('Running Identity Tool...')
        try:
            arcpy.Identity_analysis(identity_on, identity_features, output)
        except:
            print(arcpy.GetMessages())

    def add_keys(self, layer):
        '''adds fields that will contain records stored in composite key field
        '''
        print('Adding New Fields to {}...'.format(layer))
        try:
            arcpy.AddField_management(layer, 'Provider', 'TEXT', field_length=50)
            arcpy.AddField_management(layer, 'TechType', 'TEXT', field_length=10)
            arcpy.AddField_management(layer, 'MaxDown', 'Double')
            arcpy.AddField_management(layer, 'MaxUp', 'Double')
            arcpy.AddField_management(layer, 'x', 'Double')
            arcpy.AddField_management(layer, 'y', 'Double')
        except:
            print(arcpy.GetMessages())

    def populate_keys(self, layer):
        '''populates new fields with information stored in the composite key field
        '''
        print('Populating Fields With Composite Key Values for {}...'.format(layer))
        try:
            fields = ['Key', 'Provider', 'TechType', 'MaxDown', 'MaxUp', 'x', 'y', 'SHAPE@X', 'SHAPE@Y']
            getcount = arcpy.GetCount_management(layer)
            count = int(getcount.getOutput(0))
            #:  Create update cursor for feature class
            i = 0
            with arcpy.da.UpdateCursor(layer, fields) as cursor:
                #: For each row, evaluate the WELL_YIELD value (index position of 0),
                #: and update WELL_CLASS (index position of 1)
                for row in cursor:
                    if i % 1000000 == 0:
                        print('{} of {} records complete'.format(str(i), str(count)))

                    key = row[0]
                    keyList = key.split('|')
                    if len(keyList) >= 1:
                        row[1] = keyList[0]
                    if len(keyList) >= 2:
                        row[2] = keyList[1]
                    if len(keyList) >= 3:
                        row[3] = keyList[2]
                    if len(keyList) >= 4:
                        row[4] = keyList[3]

                    #:  Set x and y fields to x and y values from the shape object
                    row[5] = row[7]
                    row[6] = row[8]
                    i += 1
                    #:  Update the cursor with the updated list
                    cursor.updateRow(row)
        except:
            print(arcpy.GetMessages())

    def no_service(self, layer, identity_fc, workspace):
        '''Address Points with no service need to be associated with their area type and name, and MaxDown and MaxUp need to
        be changed from Null to 0'''
        print('Managing Address Points With No Service...')

        with arcpy.da.UpdateCursor(layer, ['MaxDown']) as cursor:
            for row in cursor:
                if row[0] is None:
                    row[0] = 0

                cursor.updateRow(row)

        with arcpy.da.UpdateCursor(layer, ['MaxUp']) as cursor:
            for row in cursor:
                if row[0] is None:
                    row[0] = 0

                cursor.updateRow(row)

        expression = 'MaxDown=0'
        no_service_fc = 'NoService'
        identity_output = 'NoService_Id'
        arcpy.FeatureClassToFeatureClass_conversion(layer, workspace, no_service_fc, expression)

        #: use identity tool to append area information to unserviced address points
        arcpy.Identity_analysis(no_service_fc, identity_fc, identity_output)

        #: join unserviced address points with area information back to Address_Service_Final
        addr_fc = feature_classes['address_points']
        fieldlist1 = [f'FID_{addr_fc}', 'CountyNbr_1', 'Area_Type_1', 'NAME_1']

        #: Step 1: Create dictionary of fields and values to be joined
        joindict = {}
        with arcpy.da.SearchCursor(identity_output, fieldlist1) as rows:
            for row in rows:
                joinval = row[0]
                val1 = row[1]
                val2 = row[2]
                val3 = row[3]
                joindict[joinval] = [val1, val2, val3]

        #: Step 2: Specify Key Value field. If it exists in target, populate new fields with appropriate values
        fieldlist2 = [f'FID_{addr_fc}', 'COUNTYNBR', 'AREA_TYPE', 'NAME']
        with arcpy.da.UpdateCursor(layer, fieldlist2) as recs:
            for rec in recs:
                keyval = rec[0]
                if keyval in joindict:
                    rec[1] = joindict[keyval][0]
                    rec[2] = joindict[keyval][1]
                    rec[3] = joindict[keyval][2]

                recs.updateRow(rec)
