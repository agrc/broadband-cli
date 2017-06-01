#For use with ArcGIS 10.4 and Python 2.7
#This script takes the results from Broadband Stats from Address Points and prepares the
#output to load into a Google spreadsheet (sorts speeds, adds nodata rows, and adds
#standard speed tiers to records)


import arcpy
import csv
from os.path import join

database = r'C:\Users\bgranberg\Documents\ArcGIS\Projects\MyProject\bbservice_f11.gdb'
target_folder = r'C:\Users\bgranberg\Documents\ArcGIS\Projects\MyProject\bbservice_f11.gdb'

upload_speeds = {
    'MaxDown': {
        0: 'Unserved',
        3: '0.76-1.4 Mbps',
        4: '1.5-2.9 Mbps',
        5: '3-5.9 Mbps',
        6: '6-9.9 Mbps',
        7: '10-24.9 Mbps',
        8: '25-49.9 Mbps',
        9: '50-99 Mbps',
        10: '100-999 Mbps',
        11: '1 Gbps or greater'
    },
    'MaxUp': {
        0: 'Unserved',
        2: '0.2-0.75 Mbps',
        3: '0.7-1.4 Mbps',
        4: '1.5-2.9 Mbps',
        5: '3-5.9 Mbps',
        6: '6-9.9 Mbps',
        7: '10-24.9 Mbps',
        8: '25-49.9 Mbps',
        9: '50-99 Mbps',
        10: '100-999 Mbps',
        11: '1 Gbps or greater'
    }
}
geometry_types = ['Area', 'County']


for speed_type in upload_speeds:
    for geometry_type in geometry_types:
        print(speed_type, geometry_type)

        csv_fields = ['AreaName', 'AreaType', 'NTIA Speed Code', 'NTIA Speed Range', 'Percentage', 'Count', 'Address Count']
        #if geometry_type == geometry_types[1]:
        #    csv_fields.remove('AreaType')

        target_path = join(target_folder, '{}_{}.csv'.format(speed_type, geometry_type))
        table = join(database, '{}_{}'.format(speed_type, geometry_type))

        data = {}
        """
        example
        {
            'Bicknell': {
                5: 188,
                6: 199
            }
        }
        """

        #: aggregate data by area
        with arcpy.da.SearchCursor(table, '*') as cur:
            if geometry_type == geometry_types[0]:
                for objectid, frequency, tier, name in cur:
                    data.setdefault(name, {})

                    data[name][tier] = frequency
            else:
                for objectid, frequency, tier, county_number, name, total in cur:
                    data.setdefault(name, {})

                    data[name][tier] = frequency

        with open(target_path, 'wb') as file:
            writer = csv.writer(file)
            writer.writerow(csv_fields)

            for name in sorted(data):
                if name is None:
                    continue

                area_dict = data[name]
                total = 0.0

                if geometry_type == geometry_types[0]:
                    area_name, area_type = name.split('|')
                else:
                    area_name = name

                #: fill in missing speeds and tally up total
                for speed in upload_speeds[speed_type]:
                    total = total + area_dict.setdefault(speed, 0)

                for tier in area_dict:
                    frequency = area_dict[tier]
                    if total > 0:
                        percentage = round(frequency/total, 3)
                    else:
                        percentage = 0

                    if geometry_type == geometry_types[0]:
                        line = [area_name, area_type, tier, upload_speeds[speed_type][tier], percentage, frequency, total]
                    else:
                        line = [area_name, "County", tier, upload_speeds[speed_type][tier], percentage, frequency, total]

                    writer.writerow(line)

print('done')
