#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      emartin
#
# Created:     05/04/2017
# Copyright:   (c) emartin 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, time, sys, os, myGlobals
import HR_DOR as hydroRout
import prepStreams as PS


from time import strftime
dateStamp= strftime("%Y%m%d_%I%M%S")
root = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), os.pardir))


myWorkspace = myGlobals.myWorkspace
sourceStreams = myGlobals.streamCATFlowlines
strUIDField = myGlobals.strUIDField
barrUIDField = myGlobals.barrUIDField
snapDist = myGlobals.snapDist
fNodeField = myGlobals.fNodeField
tNodeField = myGlobals.tNodeField
networkIDField = myGlobals.networkIDField
segmentLengthField = myGlobals.segLengthField
gdbName = myGlobals.metricsGDBFullPath

usNetID = myGlobals.barrUSNetID
dsNetID = myGlobals.barrDSNetID
usStrID = myGlobals.usStrID
dsStrID = myGlobals.dsStrID

outHRTable =myGlobals.outHRTable

arcpy.env.workspace = myWorkspace
arcpy.env.overwriteOutput = True

logger = myGlobals.rootLogger

def main(inBarriers, inStreams, outputFuncNet):
    bigStart = time.time()

    barriers, splitStreams = PS.prepRivers(inBarriers, inStreams)

    #run hydroRout for selected barriers
    numpyTable, arcHRTable = runHR(splitStreams, barriers, myWorkspace, strUIDField, "NDOID", "NUOID",  barrUIDField, 1, (strUIDField, "NDOID", "NUOID", fNodeField, tNodeField, "GNIS_Name"))
    finalFuncNet = functionalNetworks(arcHRTable, splitStreams, barriers, outputFuncNet)
    getBarrUSDSNetsNear(finalFuncNet, strUIDField, networkIDField, barriers, usNetID, dsNetID, usStrID, dsStrID)

    bigEnd = time.time()
    bigD = bigEnd-bigStart
    logger.info("Finished functional river networks analysis in {} seconds".format(bigD))
    return finalFuncNet



def uniqueTouchingBay(network):
    #HydroRout calculates all networks touching the ocean as networkID = 0.  This functional gives each topologically
    #unique network its own ID
    try:
        s= time.time()
        #get the highest batNetID, this will be the starting point for new IDs
        batNetIDs = []
        fields = myGlobals.networkIDField
        with arcpy.da.SearchCursor(network, fields) as rows:
            for row in rows:
                batNetIDs.append(row[0])
        highestBatNetID = max(batNetIDs)
        startingNewBatNetID = highestBatNetID + 1

        #buffer the networks by a small amount, dissolving on all.  Then explode them and assign each an ID
        networks0 = "{}/batNet0".format(arcpy.env.scratchGDB)
        buffDisso = "{}/buffDisso".format(arcpy.env.scratchGDB)
        exploded = "{}/exploded".format(arcpy.env.scratchGDB)
        joined = "{}/joined".format(arcpy.env.scratchGDB)
        arcpy.Select_analysis(network, networks0, "{} = 0".format(myGlobals.networkIDField))
        arcpy.DeleteField_management(networks0, myGlobals.networkIDField)
        arcpy.Buffer_analysis(in_features = networks0, out_feature_class=buffDisso, buffer_distance_or_field="0.01 Meters", dissolve_option="ALL")
        arcpy.MultipartToSinglepart_management(buffDisso, exploded)
        arcpy.AddField_management(exploded, myGlobals.networkIDField, "LONG")
        fields = myGlobals.networkIDField
        with arcpy.da.UpdateCursor(exploded, fields) as rows:
            for row in rows:
                row[0] = startingNewBatNetID
                startingNewBatNetID +=1
                rows.updateRow(row)

        #join back to source
        arcpy.MakeFeatureLayer_management(networks0, "networkLyr")
        arcpy.MakeFeatureLayer_management(exploded, "polyLyr")
        arcpy.SpatialJoin_analysis("networkLyr", "polyLyr", joined)
        newNetIDDict = {}
        fields = (myGlobals.strUIDField, myGlobals.networkIDField)
        with arcpy.da.SearchCursor(joined, fields) as rows:
            for row in rows:
                newNetIDDict[row[0]] = row[1]

        with arcpy.da.UpdateCursor(network, fields) as rows:
            for row in rows:
                if row[0] in newNetIDDict:
                    row[1] = newNetIDDict[row[0]]
                    rows.updateRow(row)

        e= time.time()
        logger.info("...finished adding network IDs to networks that touch the ocean in {} seconds".format(e-s))

    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem calculating networkIDs for networks touching the ocean on functionalNetworks line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def functionalNetworks(HRtable, riverNetwork, barriers,  outputFuncNet):
    start = time.time()
    finalFuncNet = outputFuncNet
    arcpy.CopyFeatures_management(riverNetwork, finalFuncNet)
    dictJoin("plainJoin", True, HRtable, strUIDField, finalFuncNet, strUIDField, (networkIDField,))
    end = time.time()
    duration = end-start
    logger.info("...finished exporting functional river networks  in {} seconds".format(duration))
    return finalFuncNet

def getBarrUSDSNetsNear(streams, strIDField, networkIDField, barriers, usNetField, dsNetField, usSegField, dsSegField):
    try:
        start = time.time()
        field_names = [f.name for f in arcpy.ListFields(barriers)]
        for fld in (usNetField, dsNetField):
            if fld not in field_names:
                arcpy.AddField_management(barriers, fld, "LONG")

        #populate a dictionary with all the segments and their Network_IDs
        netDict = {}
        fields =(strIDField, networkIDField)
        with arcpy.da.SearchCursor(streams, fields) as rows:
            for row in rows:
                netDict[row[0]] = row[1]

        fields = (usSegField, dsSegField, usNetField, dsNetField)
        with arcpy.da.UpdateCursor(barriers, fields) as rows:
            for row in rows:
                usSegID = row[0]
                dsSegID = row[1]
                try:
                    row[2] = netDict[usSegID]
                except:
                    row[2] = None
                try:
                    row[3] = netDict[dsSegID]
                except:
                    row[3] = None
                rows.updateRow(row)

        #Remove barriers with Nulls with US/DS Seg or US/DS NEtwork.  These are not snapped
        #and cuase problme later on
        arcpy.MakeFeatureLayer_management(barriers, "barrLyr")
        exp = "{} is null or {} is null".format(usSegField, dsSegField)
        arcpy.SelectLayerByAttribute_management("barrLyr", "NEW_SELECTION", exp)
        arcpy.DeleteFeatures_management("barrLyr")

        end = time.time()
        duration = end-start
        logger.info("...finished getting us & ds network IDs for barriers in {} seconds".format(duration))

    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="getting us & ds network IDs for barriers on functionalNetworks line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def runHR(streams, barriers, workspace, strUIDField, dnSegID, upSegID,  barrUIDField, export, keepFields):
    start = time.time()
    logger.info("Starting HydroRout...")
    arcTable, numpyTable = hydroRout.run(streams, barriers, workspace, strUIDField, dnSegID, upSegID,  barrUIDField, export, keepFields)
    # arcpy.CopyRows_management(arcTable, outHRTable)
    end = time.time()
    duration = end-start
    logger.info("...finished HydroRout in {} seconds".format(duration))


    start = time.time()
    dictJoin("plainJoin", True, arcTable, strUIDField, streams, strUIDField, (networkIDField,))
    end = time.time()
    duration = end-start
    logger.info("...finished dictionary join in {} seconds".format(duration))

    return numpyTable, arcTable


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
        valueDict = dict([(r[0], (list(r[i] for i in fieldNums))) for r in arcpy.da.SearchCursor(sourceFC, sCursorFields)])

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
                            logger.info("Join type does not match the join type options of 'plainJoin', 'addJoin', or 'timesJoin'.  Enter one fo these options and try again...")
                            sys.exit()
                else:
                    pass
            del valueDict

    except Exception as e:
        tb = sys.exc_info()[2]
        logger.warning("Problem dictionary join on line {}. {}".format(tb.tb_lineno, e))


if __name__ == '__main__':
    main()
