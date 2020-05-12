#-------------------------------------------------------------------------------
# Name:        Prep streams
# Purpose:     Steps to prepare rivers and barriers from the NHDPlus (preprocessed to a dendrite)
#               & a combined barrier dataset for the Kennebec DST - BART.
#
# Author:      emartin@tnc.org
#
# Created:     April 18, 2018
# Copyright:   (c) emartin 2018
#-------------------------------------------------------------------------------
import arcpy, time, sys, myGlobals, UpstreamIDs_PandasForLargeLayers as usIDs
from collections import defaultdict

myWorkspace = myGlobals.myWorkspace
sourceStreams = myGlobals.streamCATFlowlines
strUIDField = myGlobals.strUIDField
barrUIDField = myGlobals.barrUIDField
snapDist = myGlobals.snapDist
fNodeField = myGlobals.fNodeField
tNodeField = myGlobals.tNodeField
segmentLengthField = myGlobals.segLengthField

preppedNetwork = myGlobals.preppedNetworkFullPath
preppedBarriers = myGlobals.preppedBarriers

outHRTable =myGlobals.outHRTable
# finalFuncNet = myGlobals.finalFuncNet

logger = myGlobals.rootLogger

arcpy.env.workspace = myWorkspace
arcpy.env.overwriteOutput = True

def main():
    pass
    # prepRivers(sourceBarriers, sourceStreams)


def prepRivers(inBarriers, inStreams):
    barriers = inBarriers
    splitStreams = fracture(inStreams, barriers)
    newID(splitStreams, strUIDField)
    newNodes(splitStreams, fNodeField, tNodeField)
    upDownIDs(splitStreams, strUIDField)
    getBarrUSDSIdsNear(splitStreams, strUIDField, barriers, "usStrID", "dsStrID")
    setBarrierStreamSegID(barriers)

    # export(splitStreams, preppedNetwork, barriers, preppedBarriers)
    return barriers, splitStreams


def fracture(streams, barriers):
    try:
        #Split the streams at the barrier locations
        start = time.time()
        splitStreams ="{}/Fracture".format(myWorkspace)
        filteredStreams ="{}/filteredStreams".format(myWorkspace)
##        exp ="TotDASQKM >{} and NHDPlusID not in (5000400045695, 5000400035591, 5000400041611, 5000400041615, 5000400005104, 5000400047646)".format(minStreamDASQKM)
        exp = "1=1"
        arcpy.Select_analysis(streams, filteredStreams, exp)
        arcpy.SplitLineAtPoint_management(filteredStreams, barriers, splitStreams, "1 Meters")

        #get length of new segments
        arcpy.AddField_management(splitStreams, segmentLengthField, "DOUBLE")
        fields = ("SHAPE@LENGTH", segmentLengthField)
        with arcpy.da.UpdateCursor(splitStreams, fields) as rows:
            for row in rows:
                row[1] = row[0]/1000
                rows.updateRow(row)

        end = time.time()
        duration = end-start
        logger.info("...finished fracture in {} seconds".format(duration))
        return splitStreams

    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem running fracture on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def newID(streams, strUIDField):
    try:
        #Add a new Segment ID for each segment of the newly split streams, based on OBJECTID
        start = time.time()
        arcpy.AddField_management(streams, strUIDField, "LONG")
        fields = ("OBJECTID", strUIDField)
        with arcpy.da.UpdateCursor(streams, fields) as rows:
            for row in rows:
                row[1] = row[0]
                rows.updateRow(row)
        end = time.time()
        duration = end-start
        logger.info("...finished new stream IDs in {} seconds".format(duration))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem adding new IDs on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def newNodes(input_lines,fNodeField, tNodeField):
    try:
        #Create new From and To nodes for the newly split streams
        start = time.time()
        arcpy.AddField_management(input_lines, fNodeField, "LONG")
        arcpy.AddField_management(input_lines, tNodeField, "LONG")

        xy_dict = {}
        fields =('SHAPE@', fNodeField, tNodeField)
        with arcpy.da.UpdateCursor(input_lines, fields) as rows:
            for row in rows:
                # From Node
                from_key = '{},{}'.format(round(row[0].firstPoint.X, 7), round(row[0].firstPoint.Y, 7))
                #if xy_dict.has_key(from_key):
                if from_key in xy_dict:
                    row[1] = xy_dict[from_key]
                else:
                    row[1] = len(xy_dict) + 1
                    xy_dict[from_key] = len(xy_dict) + 1

                # To Node
                to_key = '{},{}'.format(round(row[0].lastPoint.X, 7), round(row[0].lastPoint.Y, 7))
                #if xy_dict.has_key(to_key):
                if to_key in xy_dict:
                    row[2] = xy_dict[to_key]
                else:
                    row[2] = len(xy_dict) + 1
                    xy_dict[to_key] = len(xy_dict) + 1
                rows.updateRow(row)
        end = time.time()
        duration = end-start
        logger.info("...finished making new nodes in {} seconds".format(duration))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem calcing nodes on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def upDownIDs(streams, strUIDField):
    try:
        #for each segemnt populate fields with the upstream and downstream segment IDs
        start = time.time()
        arcpy.AddField_management(streams, "NUOID", "TEXT")
        arcpy.AddField_management(streams, "NDOID", "LONG")
        usIDs.makeIDs(streams, strUIDField, "NUOID", "NDOID", fNodeField, tNodeField)
        end = time.time()
        duration = end-start
        logger.info("...finished getting stream us & ds IDs in {} seconds".format(duration))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem calcing up and down IDs on line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def getBarrUSDSIdsNear(streams, strIDField, barriers, usSegField, dsSegField):
    try:
        #For each barrier get the segment IDs of the upstream and downstream segments
        start = time.time()
        field_names = [f.name for f in arcpy.ListFields(barriers)]
        for fld in (dsSegField, usSegField):
            if fld not in field_names:
                arcpy.AddField_management(barriers, fld, "LONG")

        nearTable ="{}/barrierSegs".format(myWorkspace)
        #new IDs are the same as OBJECTID, so can just use the Near Table tool, which returns the nearest OBJECTID
        arcpy.GenerateNearTable_analysis(barriers, [streams], nearTable, "1 Meters", "NO_LOCATION", "NO_ANGLE", "ALL")

        #Populate a dict with the stream segments & their From_Node and To_Node
        strSegNodeDict = defaultdict(list)
        fields =(strIDField, fNodeField, tNodeField)
        with arcpy.da.SearchCursor(streams, fields) as rows:
            for row in rows:
                strSegNodeDict[row[0]]= [row[1], row[2]]

        #Populate a dict with the US & DS segment IDs for each barrier. Don't know which is which at this point
        barrierSegDict = defaultdict(list)
        fields =("IN_FID", "NEAR_FID")
        with arcpy.da.SearchCursor(nearTable, fields) as rows:
            for row in rows:
                barrierSegDict[row[0]].append(row[1])


        fields = (barrUIDField, dsSegField, usSegField, "OBJECTID")
        with arcpy.da.UpdateCursor(barriers, fields) as rows:
            for row in rows:
                barrID = row[0]
                usdsList = []
                for i, seg in enumerate(barrierSegDict[row[3]]):
                    #segment IDs and Fnode and TNode
                    segID =barrierSegDict[row[3]][i]
                    fNode =strSegNodeDict[segID][0]
                    tNode =strSegNodeDict[segID][1]
                    usdsList.append([segID, fNode, tNode])

                #if first segement's from node == 2nd segement's to node, then
                #first segemnt is DS and second segment is US
                try:
                    if usdsList[0][1] == usdsList[1][2]:
    ##                    logger.info("Barrier {} has DS segment {} and US segment {}".format(row[0], usdsList[0][0], usdsList[1][0]))
                        row[1]=usdsList[0][0]
                        row[2]=usdsList[1][0]
                    else:
                        row[1]=usdsList[1][0]
                        row[2]=usdsList[0][0]
                    rows.updateRow(row)
                except:
                    pass
    ##                logger.info("{} {} is not within the snap distance of a stream".format(barrUIDField, row[0]))


        end = time.time()
        duration = end-start
        logger.info("...finished barrier us & ds IDs in {} seconds".format(duration))

    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem getting US & DS barrier IDs on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def setBarrierStreamSegID(barriers):
    try:
        #For each barrier get the stream segemnt ID it is assocaited with.  This should be the upstream one
        start = time.time()
        field_names = [f.name for f in arcpy.ListFields(barriers)]
        if strUIDField in field_names:
            pass
        ##        logger.info("{} exists already".format(strUIDField))
        else:
            arcpy.AddField_management(barriers, strUIDField, "LONG")

        fields =(strUIDField, "usStrID")
        with arcpy.da.UpdateCursor(barriers, fields) as rows:
            for row in rows:
                row[0] = row[1]
                rows.updateRow(row)

        end = time.time()
        duration = end-start
        logger.info("...finished setting barrier stream segment IDs in {} seconds".format(duration))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem setting stream barrier segment on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def export(instreams, outstreams, inbarriers, outbarriers):
    try:
        #Export the prepped data
        start = time.time()
        arcpy.CopyFeatures_management(instreams, outstreams)
        arcpy.CopyFeatures_management(inbarriers, outbarriers)

        end = time.time()
        duration = end-start
        logger.info("...finished exporting in {} seconds".format(duration))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem exporting on prepStreams line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


if __name__ == '__main__':
    main()

