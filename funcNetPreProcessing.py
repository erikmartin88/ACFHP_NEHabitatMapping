import sys, os, arcpy, myGlobals as mg
import collections
import functionalNetworks as FN
catchments = mg.streamCATCatchments

logger = mg.rootLogger


def makeFuncNets():
    try:
        dendrite = functionalNetworkPrep(mg.dendrite)
        inputBarriers = copyInputBarriers(mg.regionalBarriers)
        useBarriers = snapBarriers(inputBarriers, dendrite)
        funcNet = runFunctionalNetworks(useBarriers, dendrite)
        return funcNet, useBarriers
    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running anadromous presence metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def functionalNetworkPrep(dendrite):
    try:
        outGDB = mg.metricsGDBFullPath
        logger.info("Prepping data for functional network generation...")

        #Copy hydrography
        outDend = os.path.join(outGDB,  "Dendrite")
        arcpy.CopyFeatures_management(dendrite, outDend)
        keepFields = ("OBJECTID", "SHAPE", "COMID", "FDATE", "GNIS_NAME", "GNIS_ID", "LENGTHKM", "FLOWDIR", "REACHCODE", "FTYPE", "FCODE", "ENABLED", "SHAPE_Length", "Shape_Length", "Shape")
        deleteFields = []
        fields = arcpy.ListFields(outDend)
        for field in fields:
            if field.name not in keepFields:
                deleteFields.append(field.name)
        if len(deleteFields)>0:
            arcpy.DeleteField_management(outDend, deleteFields)
        arcpy.AddField_management(outDend, "HYDROID", "LONG")
        arcpy.CalculateField_management(outDend, "HYDROID", "!OBJECTID!", "PYTHON")

        return(outDend)

        logger.info("...Successfully finished prepping data for functional network generations...")

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem with functional network prep on line {} of funcNetPreProcessing. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def copyInputBarriers(sourceBarriers):
    try:
        inputDams = os.path.join(mg.metricsGDBFullPath, "inputDams")
        arcpy.Select_analysis(sourceBarriers, inputDams, "Type='Dam' AND Use=1")
        return inputDams
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem prepping barriers on line {} of funcNetPreProcessing. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def snapBarriers(barriers, streams):
    try:
        logger.info("Snapping barriers...")
        arcpy.Snap_edit(barriers, [[streams, "EDGE", mg.snapDist]])
        arcpy.AddField_management(barriers, "Use", "SHORT")
        barrLyr = "barriers_lyr"
        arcpy.MakeFeatureLayer_management(barriers, barrLyr)
        arcpy.SelectLayerByLocation_management(barrLyr, "INTERSECT", streams, "", "NEW_SELECTION")
        arcpy.CalculateField_management(barrLyr, "Use", 1, "PYTHON")
        arcpy.SelectLayerByAttribute_management(barrLyr, "SWITCH_SELECTION")
        arcpy.CalculateField_management(barrLyr, "Use", 2, "PYTHON")
        arcpy.SelectLayerByAttribute_management(barrLyr, "CLEAR_SELECTION")

        #identify those barriers that are snapped to an end and move them.
        logger.info("...moving barriers on segment end nodes...")
        buff = "{}/barrierBuff".format(mg.myWorkspace)
        buffLine = "{}/barrierBuffOutline".format(mg.myWorkspace)
        upDownPoints = "{}/barrierBuffPtIntersect".format(mg.myWorkspace)
        upDownPoints_exp = "{}/barrierBuffPtIntersectExplode".format(mg.myWorkspace)
        arcpy.Buffer_analysis(barriers, buff, "1 Meters")
        arcpy.PolygonToLine_management(buff, buffLine)
        mg.dictJoin("plainJoin", True, buff,  "OBJECTID", buffLine, "RIGHT_FID", [mg.barrUIDField])
        arcpy.Intersect_analysis([buffLine, streams], upDownPoints, "ALL", "", "POINT")
        arcpy.MultipartToSinglepart_management(upDownPoints, upDownPoints_exp)
        upDownPtList = []
        fields = (mg.barrUIDField)
        with arcpy.da.SearchCursor(upDownPoints_exp, fields) as rows:
            for row in rows:
                upDownPtList.append(row[0])
        #https://stackoverflow.com/questions/9835762/how-do-i-find-the-duplicates-in-a-list-and-create-another-list-with-them
        barrsOnEnds = [item for item, count in collections.Counter(upDownPtList).items() if count == 1]
        endBarriers = "{}/barriersOnSegEndsMoveHere".format(mg.myWorkspace)
        barrsOnEnds =  str([str(r) for r in barrsOnEnds]).replace("[", "").replace("]", "")
        exp = "{} in ({})".format(mg.barrUIDField, barrsOnEnds)
        print(exp)
        arcpy.Select_analysis(upDownPoints, endBarriers, exp)
        arcpy.Snap_edit(barriers, [[endBarriers, "VERTEX", "2 METERS"]])

        useBarriers = "{}_Use".format(barriers)
        arcpy.Select_analysis(barriers, useBarriers, "Use = 1")

        return useBarriers
    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem snapping barriers on line {} of funcNetPreProcessing. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def runFunctionalNetworks(barriers, streams):
    try:
        logger.info("Starting functional network generation...")
        finalFuncNet = os.path.join(mg.metricsGDBFullPath, "FunctionalRiverNetwork")
        funcNet = FN.main(barriers, streams,  finalFuncNet)
        return funcNet

    except Exception as e:
        tb = sys.exc_info()[2]
        msg ="Problem generating functional networks on line {} of funcNetPreProcessing. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()