#For use with ArcPro 1.4 and Python 3.5

###This script calculates maximum upload and download speeds for each address, and the number of addresses in different administrative boundaries
#Broadband data is associated with address points using a Pairwise Intersect tool and an Identity tool
#Two functions Analysis() and Statistics() are called that nest all the other functions
#The output tables from Statistics() can be used in the "BBStats_query" script for further statistics
#Total runtime varies between 2-4 hours

import arcpy

#define workspace geodatabse
arcpy.env.workspace = r"C:\Users\bgranberg\Documents\ArcGIS\Projects\MyProject\bbservice_s12.gdb"
workspace = arcpy.env.workspace
arcpy.env.overwriteOutput = True

#define paths to input data from SGID10 and UBBADMIN databases
BB_Service = "BB_Service"
AddressPoints = "AddressPoints"
Counties = "Counties"
Municip = "Municipalities"
Unincorp = "UnIncorpAreas2010_Approx"

#define path to toolbox containing custom Pairwise Intersect Tool (http://www.arcgis.com/home/item.html?id=120807ac7f8449f89840ae48e87d7f55)
#pairwise_tbx = "C:\Broadband\Data\Stats\PairwiseIntersectTool\PairwiseIntersectTool\Pairwise.tbx"

#A variable for the output of the indentity function and an input for subsequent functions
#Leave This Alone
Address_Service_Final = "Address_Service_Final"



def Analysis_Areas1(Counties, Municip, Unincorp):
    #create area types for analysis
    print ("Creating Analysis_Areas Layer...")
    try:
        arcpy.Union_analysis([Municip,Unincorp], "Not_Counties")
        arcpy.Erase_analysis(Unincorp, Municip, "Unincorporated")       #Unincorporated
        arcpy.Erase_analysis(Counties, "Not_Counties", "Other")          #Counties
        arcpy.Delete_management("Not_Counties")
        #redefine variables with new data
        Other = "Other"
        Unincorp = "Unincorporated"

       #add new field "Type" to each area category and populate with type name
        arcpy.AddField_management(Other, "Area_Type", "TEXT")
        with arcpy.da.UpdateCursor(Other, "Area_Type") as cursor:
            for row in cursor:
                row[0] = "Other"
                cursor.updateRow(row)
        arcpy.AddField_management(Municip, "Area_Type", "TEXT")
        with arcpy.da.UpdateCursor(Municip, "Area_Type") as cursor:
            for row in cursor:
                row[0] = "Municipality"
                cursor.updateRow(row)
        arcpy.AddField_management(Unincorp, "Area_Type", "TEXT")
        with arcpy.da.UpdateCursor(Unincorp, "Area_Type") as cursor:
            for row in cursor:
                row[0] = "Unincorporated"
                cursor.updateRow(row)

    #Create "Analysis_Areas" feature class
        arcpy.AlterField_management(Unincorp, "PLACENAME", "NAME")         #Name field must be the same across all three feature classes
        arcpy.Append_management([Other, Municip], Unincorp, "NO_TEST")  #Append counties and municipalities to Analysis_Areas (unincorp features)
        if arcpy.Exists("Analysis_Areas"):                                 #Rename Unincorp to Analysis_Areas
            arcpy.Delete_management("Analysis_Areas")                         #Note: This if/else seems redundant with overwriteOutput = True, but
            arcpy.Rename_management(Unincorp, "Analysis_Areas")               #there were bugs regardless. This chunk took care of whatever was wrong
        else:
            arcpy.Rename_management(Unincorp, "Analysis_Areas")
        arcpy.Delete_management("Other")
    except:
        print (arcpy.GetMessages())



def Composite_Key(BB_Service):
    #create composite key values in BB_Service
    print ("Creating Composite Key...")
    try:
        expression = "!UTProvCode! + '|' + str(!TRANSTECH!) + '|' + str(!MAXADDOWN!) + '|' + str(!MAXADUP!)"
        arcpy.AddField_management(BB_Service, "Key", "TEXT", 70)
        arcpy.CalculateField_management(BB_Service, "Key", expression, "PYTHON_9.3")
        #Dissolve features based on the composite key
        arcpy.Dissolve_management(BB_Service, "BB_Service_Dissolve", "Key")
    except:
        print (arcpy.GetMessages())


def Pairwise_Intersect():
    #intersects BB service areas against Analysis areas, creating unique polygons in BB_Service_Dissolve
    #for each type in Analysis_Areas
    print ("Running Pairwise Intersection Tool...")
    try:
        fields = ["CountyNbr", "NAME", "Area_Type", "Shape_Length", "Shape_Area"]
        inFeatures = ["BB_Service_Dissolve", "Analysis_Areas"]
        arcpy.PairwiseIntersect_analysis(inFeatures, "BB_Service_Dissolve_Pairwise")
    except:
        print (arcpy.GetMessages())


def Identity(AddressPoints):
    #attaches composite key values to AddressPoints based on their relationships to BB Service areas
    print ("Running Identity Tool...")
    try:
        arcpy.Identity_analysis(AddressPoints, "BB_Service_Dissolve_Pairwise", Address_Service_Final)
    except:
        print(arcpy.GetMessages())


def Add_Keys(Address_Service_Final):
    #adds fields that will contain records stored in composite key field
    print ("Adding New Fields...")
    try:
        arcpy.AddField_management(Address_Service_Final, "Provider", "TEXT", field_length = 50)
        arcpy.AddField_management(Address_Service_Final, "TechType", "TEXT", field_length = 10)
        arcpy.AddField_management(Address_Service_Final, "MaxDown", "Double")
        arcpy.AddField_management(Address_Service_Final, "MaxUp", "Double")
        arcpy.AddField_management(Address_Service_Final, "x", "Double")
        arcpy.AddField_management(Address_Service_Final, "y", "Double")
    except:
        print (arcpy.GetMessages())


def Populate_Keys(Address_Service_Final):
    #populates new fields with information stored in the composite key field
    print ("Populating Fields With Composite Key Values...")
    try:
        fields=["Key", "Provider","TechType","MaxDown","MaxUp", "x", "y", "SHAPE@X", "SHAPE@Y"]
        getcount = arcpy.GetCount_management(Address_Service_Final)
        count = int(getcount.getOutput(0))
        # Create update cursor for feature class
        i=0
        with arcpy.da.UpdateCursor(Address_Service_Final, fields) as cursor:
        # For each row, evaluate the WELL_YIELD value (index position
        # of 0), and update WELL_CLASS (index position of 1)
            for row in cursor:
                if i%1000000==0:
                    print (str(i) + " of " + str(count) + " records complete")
                key=row[0]
                keyList=key.split("|")
                if len(keyList)>=1:
                   row[1]= keyList[0]
                if len(keyList)>=2:
                   row[2]= keyList[1]
                if len(keyList)>=3:
                   row[3]= keyList[2]
                if len(keyList)>=4:
                   row[4]= keyList[3]
                # Set x and y fields to x and y values from the shape object
                row[5] = row[7]
                row[6] = row[8]
                i+=1
                # Update the cursor with the updated list
                cursor.updateRow(row)
    except:
        print (arcpy.GetMessages())


def NoService():
    #Address Points with no service need to be associated with their area type and name, and MaxDown and MaxUp need to
    #be changed from Null to 0

    print ("Managing Address Points With No Service...")
    with arcpy.da.UpdateCursor(Address_Service_Final, ["MaxDown"]) as cursor:
        for row in cursor:
            if row[0] == None:
                row[0] = 0
            cursor.updateRow(row)
    with arcpy.da.UpdateCursor(Address_Service_Final, ["MaxUp"]) as cursor:
        for row in cursor:
            if row[0] == None:
                row[0] = 0
            cursor.updateRow(row)
    expression = "MaxDown = 0"
    arcpy.FeatureClassToFeatureClass_conversion(Address_Service_Final, workspace, "NoService", expression)
    #use identity tool to append area information to unserviced address points
    arcpy.Identity_analysis("NoService", "Analysis_Areas", "NoService_id")
    #join unserviced address points with area information back to Address_Service_Final
    target = "Address_Service_Final"
    join = "NoService_id"
    fieldlist1 = ["FID_AddressPoints", "CountyNbr_1", "Area_Type_1", "NAME_1"]
    ## Step 1: Create dictionary of fields and values to be joined
    joindict = {}
    with arcpy.da.SearchCursor(join, fieldlist1) as rows:
        for row in rows:
            joinval = row[0]
            val1 = row[1]
            val2 = row[2]
            val3 = row[3]
            joindict[joinval]=[val1,val2,val3]
    ## Step 2: Specify Key Value field. If it exists in target, populate new fields with appropriate values
    fieldlist2 = ["FID_AddressPoints", "COUNTYNBR", "AREA_TYPE", "NAME"]
    with arcpy.da.UpdateCursor(target, fieldlist2) as recs:
        for rec in recs:
            keyval = rec[0]
            if keyval in joindict:
                rec[1] = joindict[keyval][0]
                rec[2] = joindict[keyval][1]
                rec[3] = joindict[keyval][2]
            recs.updateRow(rec)




def JoinTables():
    #join area data (area name, type, county) to MSBA statistics generated above
    #this custom join function is much faster than the JoinField tool

    target = "MSBA"
    join = "Address_Service_Final"
    fieldlist = ["FID_AddressPoints", "NAME", "AREA_TYPE", "COUNTYNBR"]
## Step 1: Create dictionary of fields and values to be joined
    joindict = {}
    with arcpy.da.SearchCursor(join, fieldlist) as rows:
        for row in rows:
            joinval = row[0]
            val1 = row[1]
            val2 = row[2]
            val3 = row[3]
            joindict[joinval]=[val1,val2,val3]
    arcpy.AddField_management(target, "NAME", "TEXT")
    arcpy.AddField_management(target, "AREA_TYPE", "TEXT")
    arcpy.AddField_management(target, "COUNTYNBR", "TEXT")
## Step 2: Specify Key Value field. If it exists in target, populate new fields with appropriate values
    with arcpy.da.UpdateCursor(target, fieldlist) as recs:
        for rec in recs:
            #import pdb; pdb.set_trace()
            keyval = rec[0]
            if keyval in joindict:
                rec[1] = joindict[keyval][0]
                rec[2] = joindict[keyval][1]
                rec[3] = joindict[keyval][2]
            recs.updateRow(rec)



def MaxSpeeds(data):
    #find maximum download and upload speed for each address ( ~ 10 Minutes)
    print ("Calculating Maximum Upload and Download Speeds for Addresses...")
    try:
        arcpy.Statistics_analysis(data, "MSBA",[["MaxDown", "MAX"],["MaxUp", "MAX"]] , "FID_AddressPoints")
    except:
        print (arcpy.GetMessages())
    try:
        JoinTables() #calls function above. Adds new Max statistics back to main data table (~ 5 minutes)
    except:
        print (arcpy.GetMessages())




def AddressCounts(MSBA):
    #find number of address points in each area by name.
    #A new field "Name_Area" is specified due to duplicate names (Emery=County and Emery=Municipality) This is
    #important when running query script
    print ("Calculating Address Count By Area Name...")
    try:
        arcpy.AddField_management(MSBA, "Name_Area", "Text")
        with arcpy.da.UpdateCursor(MSBA, ["Name_Area", "NAME", "AREA_TYPE"]) as cursor:
            for row in cursor:
                row[0] = row[1] + "|" + row[2]
                cursor.updateRow(row)
        arcpy.Statistics_analysis(MSBA, "AddressCount_AreaName", [["FID_AddressPoints", "Count"]], ["Name_Area"])
    except:
        print (arcpy.GetMessages())
    #find number of address points in each area by area type (Municipality, Unincorporated, Other)
    print ("Calculating Address Count By Area Type...")
    try:
        arcpy.Statistics_analysis("MSBA", "AddressCount_AreaType", [["FID_AddressPoints", "Count"]], ["AREA_TYPE"])
    except:
        print (arcpy.GetMessages())
    #find number of address points in each area by County
    #The "other" category only represents County area that is not a municipality or unincorporated.
    #This step gets an address count using the entire County's area
    print ("Calculating Address Count By County...")
    try:
        arcpy.Statistics_analysis("MSBA", "AddressCount_County", [["FID_AddressPoints",  "Count"]], ["COUNTYNBR"])
    except:
        print (arcpy.GetMessages())


def SpeedTiers(table): # ~ 5 Minutes
    #Calculates Speed Tiers for MaxDown and MaxUp Speeds
    print ("Calculating Speed Tiers...")
    arcpy.AddField_management(table, "MaxDown_Tier", "Short")
    arcpy.AddField_management(table, "MaxUp_Tier", "Short")
    with arcpy.da.UpdateCursor(table, ["MAX_MaxDown", "MaxDown_Tier"]) as cursor:
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
    with arcpy.da.UpdateCursor(table, ["MAX_MaxUp", "MaxUp_Tier"]) as cursor:
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

def SpeedCounts():
    #Calculates number of address points in each speed tier for:
    #Counties
    print ("Calculating Speed Tier Statistics for Counties...")
    arcpy.Frequency_analysis("MSBA", "MaxDown_County", ["MaxDown_Tier", "COUNTYNBR"])
    arcpy.Frequency_analysis("MSBA", "MaxUp_County", ["MaxUp_Tier", "COUNTYNBR"])
    tablelist = ["MaxDown_County", "MaxUp_County"]
    for table in tablelist:
        arcpy.JoinField_management(table, "COUNTYNBR", Counties, "COUNTYNBR", ["NAME"])
        arcpy.JoinField_management(table, "COUNTYNBR", "AddressCount_County", "COUNTYNBR", ["COUNT_FID_AddressPoints"])
    #Named Areas (Municipalities, Unincorporated, Other)
    print ("Calculating Speed Tier Statistics for Areas...")
    arcpy.Frequency_analysis("MSBA", "MaxDown_Area", ["MaxDown_Tier", "Name_Area"])
    arcpy.Frequency_analysis("MSBA", "MaxUp_Area", ["MaxUp_Tier", "Name_Area"])



#Call these functions to run part/all of script

def Analysis():
    Analysis_Areas1(Counties, Municip, Unincorp)
    #Analysis_Areas2()
    Composite_Key(BB_Service)
    Pairwise_Intersect()
    Identity(AddressPoints)
    Add_Keys(Address_Service_Final)
    Populate_Keys(Address_Service_Final)
    NoService()


def Statistics():
    MaxSpeeds(Address_Service_Final)
    AddressCounts("MSBA")
    SpeedTiers("MSBA")
    SpeedCounts()

Analysis()
Statistics()
