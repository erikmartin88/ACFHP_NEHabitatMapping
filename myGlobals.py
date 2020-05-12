#-------------------------------------------------------------------------------
# Name:        Global variables for ACFHP Northeast Diadromous Fish & Estuarine Prioritizations
# Purpose:      store gloabl variables for use across modules of the ACFHP Northeast Prioritizations
#
# Author:      emartin@tnc.org
#
# Created:     July 2019
#-------------------------------------------------------------------------------

import logging, datetime, os, sys, arcpy
from time import strftime

dateStamp= strftime("%Y%m%d_%H%M%S")

scriptPath = sys.path[0]
primeFolder = os.path.dirname(scriptPath)
GDBName = "ACFHP_NortheastPrioritization.gdb"
metricsGDBFullPath = os.path.join(primeFolder, GDBName)
snapDist = "100 METERS"
myWorkspace = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\scritch.gdb" #"in_memory"
nad83albers = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\Scripts\NAD_1983_Albers.prj"


#Diadromous input data
regionalBarriers = r"K:\NAACC\CurrentData.gdb\RegionBarriers_current"
anadromousSppHab = r"K:\NAACC\CurrentData.gdb\RegionAnadFish_current"
dendrite = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\ACFHP_ProjectDendrite"
nhdSourceFlowlines = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\NHDFlowlines_source"
nhdVAA = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\PlusFlowlineVAA"
streamCATCatchments = os.path.join(metricsGDBFullPath, "NHDPlus_v2_cat")
catchmentsGrid = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\catchment_gr"
streamCATFlowlines = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\StreamCatFlowlines"
streamCATImprvTbl = r"K:\RegionalDatasets\StreamCat\StreamCAT_Region0102.gdb\ImperviousSurfaces2011"
streamCATPointSourceTbl = r"K:\RegionalDatasets\StreamCat\StreamCAT_Region0102.gdb\EPA_FRS"
streamCATMines = r"K:\RegionalDatasets\StreamCat\StreamCAT_Region0102.gdb\Mines"
streamCATDamsFlowAlt = r"K:\RegionalDatasets\StreamCat\StreamCAT_Region0102.gdb\Dams"
nlcd2016 = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\nlcd2016"
imprv2016 = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\imprv2016"
ara = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\ARA"
ara_gr = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\ara_RC"
rdStrXings = r"K:\NAACC\CurrentData.gdb\link_crossing_xyJoined"
salmCritHab = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\CriticalHabitat\NOAA_GARFO_CriticalHabitat_061919.gdb\critical_habitat_by_HUC10"
sturgCritHab = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\CriticalHabitat\NOAA_GARFO_CriticalHabitat_061919.gdb\Atlantic_Sturgeon_Critical_Habitat_River_Lengths"
fdr = r"K:\RegionalDatasets\NHD\NHDPlus\NHDPlus_v21_EasternUSMerge.gdb\fdr"
geoNetFD = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\Hydro"
geoNetName = "GeoNetFull"
geoNet = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\Hydro\GeoNetFull"

#Estuarine input data
hexagons = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\EstuarineHexagons_Use"
sav = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\SAV\MergedSAV.gdb\acfhp_sav"
oysterReefMussel = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\OystersBlueMussels_NEOceanDataPortal"
cmec_oysters = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\CMECS_Oysters"
delawareBayOyster = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\DelawareBayOyster"
rutgersNJOys = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\RutgersNJ_OysMedHigh"
vosaraOysters = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\vosaraOysters"
# ctOys = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\CT_ShellsfishBeds_Natural" #do not use per Aaron Kornbluth / Tessa Getchis at CT Sea Grant
nwi = r"K:\RegionalDatasets\NWI\EastRegion.gdb\NWI_Merge_061419"
nwi_estuarine_agg = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\NWI_Estuarine_Aggregate"
protectedAreas = r"K:\RegionalDatasets\PAD_US\PADUS2_0.gdb\Terrestrial_GAP123"
noaaESI = r"K:\RegionalDatasets\NOAA\ESI\GULF_ATLANTIC_ESI.gdb\GULF_ATLANTIC_ESI"
ports = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\ACFHP_NortheastPrioritization.gdb\USDOT_Ports"
water303dPolys = r"K:\RegionalDatasets\NHD\303d\rad_303d_20130102.gdb\rad_303d_a"
roads = r"K:\RegionalDatasets\roads\TIGER\tlgdb_2018_a_us_roads.gdb\Roads_NAD83_Albers"
estuarineWetlandSQL = "ATTRIBUTE LIKE 'E2%'"

#hydro fields
strUIDField = "HYDROID"
strOrigIDField = "COMID"
barrUIDField = "UNIQUE_ID"
barrNameField = "DAM_NAME"
snapDist ="100 Meters"
fNodeField = "From_Node"
tNodeField = "To_Node"
networkIDField = "batNetID"
barrUSNetID = "batUSNetID"
barrDSNetID = "batDSNetID"
segLengthField = "LENGTHKM"
usStrID = "usStrID" #name of US segmentID field given to barriers
dsStrID = "dsStrID" #name of DS segmentID field given to barriers
preppedNetworkFullPath = "{}/preppedNetwork".format(metricsGDBFullPath)
preppedBarriers ="{}/preppedBarriers".format(metricsGDBFullPath)
outHRTable = "{}/OutputHR_Networks".format(metricsGDBFullPath)
outputBarriers ="{}/Output_Barriers".format(metricsGDBFullPath)

#------------set up logging
today = str(datetime.datetime.now()).split(' ')[0].strip()
logDir = os.path.join(primeFolder, "LogFiles")
logFileName = "ACFHP_{}.log".format(today.replace("-", "_"))
logFile = os.path.join(logDir, logFileName)
logFormatter = logging.Formatter(fmt='%(asctime)s | %(levelname)s | %(message)s',datefmt='%H:%M:%S')
rootLogger = logging.getLogger()
fileHandler = logging.FileHandler(logFile)
fileHandler.setFormatter(logFormatter)
rootLogger.level = logging.INFO
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

def dictJoin(joinType, addField, sourceFC,  sourceJoinField, updateFC, updateJoinField, fields):
    """
        joinType: 'plainJoin', 'addJoin' or 'timesJoin' to either join in the updated field, or add or multiple join value by existing value
        addField: boolean whether field has to be added to update table -- faster if False
        sourceFC: the feature class that has the fields to be joined
        sourceJoinField: the field from the source FC that will be used ot make the join
        updateFC: the feature class that will have values added to it
        updateJoinField: the field from the updateFC that is used to make the join
        fields: fields to be joined-- as a list - must add a trailing comma if only one field
    """
    try:
        print("Running dictionary Join  at {}...".format(stamp()))
        #add new empty fields
        if addField == True:
            fieldsToAdd = arcpy.ListFields(sourceFC)
            for fieldToAdd in fieldsToAdd:
                if fieldToAdd.name in fields:
                    arcpy.AddField_management(updateFC, fieldToAdd.name, fieldToAdd.type)

        #get the number of join fields and add on the source join ID
        numJoinFields = len(fields)
        sCursorFields = [sourceJoinField] + list(fields)
        fieldNums = list(range(1, numJoinFields + 1))

        #populate the dict with the source join ID and fields to Join
        print("...Populating valueDict at {}...".format(stamp()))
        valueDict = dict([(r[0], (list(r[i] for i in fieldNums))) for r in arcpy.da.SearchCursor(sourceFC, sCursorFields)])

        print("...Updating values in join at {}...".format(stamp()))
        uCursorFields = [updateJoinField] + list(fields)
        with arcpy.da.UpdateCursor(updateFC, uCursorFields) as updateRows:
            for updateRow in updateRows:
                joinFieldValue = updateRow[0]
                if joinFieldValue in valueDict and joinFieldValue != None:
                    i = 1
                    while i <= numJoinFields:
                        if joinType == "plainJoin":
                            updateRow[i] = valueDict[joinFieldValue][i-1]
                            updateRows.updateRow(updateRow)
                            i +=1
                        elif joinType == "addJoin":
                            updateRow[i] = updateRow[i] + valueDict[joinFieldValue][i-1]
                            updateRows.updateRow(updateRow)
                            i +=1
                        elif joinType == "timesJoin":
                            updateRow[i] = updateRow[i] * valueDict[joinFieldValue][i-1]
                            updateRows.updateRow(updateRow)
                            i +=1
                        elif joinType == "custom":
                            pass
                        else:
                            print("Join type does not match the join type options of 'plainJoin', 'addJoin', or 'timesJoin'.  Enter one fo these options and try again...")
                            sys.exit()
                else:
                    pass
            del valueDict

    except Exception as e:
        tb = sys.exc_info()[2]
        print ("Problem dictionary join on line {} at {}".format(tb.tb_lineno, stamp()))
        print(str(e))

def stamp():
    myNow = str(datetime.datetime.now()).split('.')[0]
    return myNow

def replaceNumericalNulls(fc, fields="All", replaceVal=0):
    """
    fc: the featureClass to process
    fields: LIST of the numerical fields which will have their Nulls replace with 0s. Defaults to all numerical fields.
    replaceVal : the values to replace.  Defaults to 0, but can be something else
    """
    try:
        if fields == "All":
            print("Converting Null values for ALL fields...")
            smallIntFieldList = arcpy.ListFields(fc,"","SmallInteger")
            intFieldList = arcpy.ListFields(fc,"","Integer")
            singleFieldList = arcpy.ListFields(fc,"","Single")
            doubleFieldList = arcpy.ListFields(fc,"","Double")
            fieldsToProcess = smallIntFieldList + intFieldList + singleFieldList + doubleFieldList
        else:
            print("Converting Null values for the following fields {}...".format(fields))
            fieldsToProcess = fields

        for field in fieldsToProcess:
            if fields == "All":
                name = field.name
            else:
                name = field
            with arcpy.da.UpdateCursor(fc, name, "\"{}\" IS NULL".format(name)) as rows:
                for row in rows:
                    row[0] = replaceVal
                    rows.updateRow(row)

    except Exception as e:
        tb = sys.exc_info()[2]
        print ("Problem replacing nulls on line {} at {}".format(tb.tb_lineno, stamp()))
        print(str(e))
        sys.exit()