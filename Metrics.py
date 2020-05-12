#-------------------------------------------------------------------------------
# Name:        ACFHP Northeast Diadromous Fish Prioritization Metrics
# Purpose:     Script to generate metrics to prioritize river reaches & estuarine hexagons in the Northeast
#              U.S. for diadromous fish restoration activities funded by the
#              Atlantic Coast Fish Habitat Partnership
# Author:      Erik Martin, emartin@tnc.org
#
# Created:     July 2019
#-------------------------------------------------------------------------------

import sys, os, arcpy, time, myGlobals as mg, datetime, PyRank_Module as PYM, Tier_Module as TM, funcNetPreProcessing as fnPP
from arcpy.sa import *
from collections import defaultdict



testing = 0

logger = mg.rootLogger
workspace = mg.metricsGDBFullPath

##Environments
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

def main():
    try:
        logger.info("Starting metric calculations...")
        regions = ("North_Atlantic",  "Mid_Atlantic")
        for region in regions:
            logger.info("Pulling out regions to run separately...")
            catchments = os.path.join(mg.metricsGDBFullPath, "catchments_{}".format(region))
            hexagons = os.path.join(mg.metricsGDBFullPath, "hexagons_{}".format(region))
            if arcpy.Exists(catchments) == False:
                print("making catchments")
                arcpy.Select_analysis(mg.streamCATCatchments, catchments, "Region = '{}'".format(region))
            else:
                print("updating existing catchment layer")
            if arcpy.Exists(hexagons) == False:
                print("making hexagons")
                arcpy.Select_analysis(mg.hexagons, hexagons, "Region = '{}'".format(region))
            else:
                print("updating existing hexagon layer")

            diadromous(catchments, region)
            estuarine(hexagons, region)

        #make merged mid-atlantic / north atlantic dataset
        logger.info("Making merged layers...")
        mergedCatchments = os.path.join(mg.metricsGDBFullPath, "catchments_merged")
        mergedHexagons = os.path.join(mg.metricsGDBFullPath, "hexagons_merged")
        arcpy.Merge_management(["catchments_Mid_Atlantic", "catchments_North_Atlantic"], mergedCatchments)
        arcpy.Merge_management(["hexagons_Mid_Atlantic", "hexagons_North_Atlantic"], mergedHexagons)
        makeMapServiceLayers(mergedCatchments, r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\FinalProducts\OutputMaps\FinalLayers.gdb")
        makeMapServiceLayers(mergedHexagons, r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\FinalProducts\OutputMaps\FinalLayers.gdb")

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running main() data on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def diadromous(catchments, region):
    try:
        logger.info("Starting diadromous calculations...")
        anadPres(catchments)
        imperv(catchments, region)
        pointSource(catchments)
        nonPointSource(catchments, region)
        riparianBuffer(catchments, region)
        esaCriticalHabitat(catchments)
        flowAlteration(catchments)
        fragmentation(catchments, region)

        totalPoints(catchments)
        makeMapServiceLayers(catchments, r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\FinalProducts\OutputMaps\FinalLayers.gdb")
    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running diadromous() on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def estuarine(hexagons, region):
    try:
        logger.info("Starting estuarine calculations...")
        savOys(hexagons, region)
        wetlands(hexagons, region)
        hardShore(hexagons, region)
        waterVegEdge(hexagons, region)
        habitatFragmentation(hexagons, region)
        devDistance(hexagons, region)
        protectedArea(hexagons, region)
        waterQuality(hexagons)

        totalPoints(hexagons)
        makeMapServiceLayers(hexagons, r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\FinalProducts\OutputMaps\FinalLayers.gdb")

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running estuarine() on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


#########  Diadromous #####################

def anadPres(catchments):
    try:
        #id catchments with no dams downstream
        logger.info("Starting Potential Anadromous fish presence metric...")
        if testing == 1:
            funcNet = os.path.join(mg.metricsGDBFullPath, "FunctionalRiverNetwork")
            barriers = os.path.join(mg.metricsGDBFullPath, "inputDams_Use")
        else:
            funcNet, barriers = fnPP.makeFuncNets()

        logger.info("...counting dams DS of each catchment...")
        countDS(barriers, mg.barrUIDField, mg.barrUSNetID, mg.barrDSNetID)

        networkCountDS = {}
        fields = (mg.barrUSNetID, "batCountDS")
        with arcpy.da.SearchCursor(barriers, fields) as rows:
            for row in rows:
                networkCountDS[row[0]] = row[1] +1

        arcpy.AddField_management(funcNet, "batCountDS", "SHORT")
        fields = (mg.networkIDField, "batCountDS")
        with arcpy.da.UpdateCursor(funcNet, fields) as rows:
            for row in rows:
                if row[0] in networkCountDS:
                    row[1] = networkCountDS[row[0]]
                else:
                    row[1] = 0
                rows.updateRow(row)

        catchmentDSDams = defaultdict(list)
        fields = (mg.strOrigIDField, "batCountDS")
        with arcpy.da.SearchCursor(funcNet, fields) as rows:
            for row in rows:
                catchmentDSDams[row[0]].append(row[1])
        numDSDams = {}
        for k, v in catchmentDSDams.iteritems():
            numDSDams[k] = max(v)  #if a COMID segment is broken by a dam, count it as having that dam downstream of it.

        logger.info("...calculating catchments with current anadormous habitat...")
        anadPres = "anadPres"
        arcpy.MakeFeatureLayer_management(mg.anadromousSppHab, anadPres, "alewife=1 OR amshad=1 OR blueback=1 OR hickshad=1 OR strbass=1 OR atlstur=1 OR atlsalm=1")
        arcpy.AddField_management(catchments, "anadPres", "SHORT")
        arcpy.CalculateField_management(catchments, "anadPres", 0, "PYTHON")
        catchLyr = "catchLyr"
        arcpy.MakeFeatureLayer_management(catchments, catchLyr)
        arcpy.SelectLayerByLocation_management(catchLyr, "INTERSECT", anadPres)
        arcpy.CalculateField_management(catchLyr, "anadPres", 1, "PYTHON")

        logger.info("...calculating final potential anadromous metric...")
        arcpy.AddField_management(catchments, "potentialAnadromousPoints", "SHORT")
        fields = (mg.strOrigIDField, "anadPres", "potentialAnadromousPoints")
        with arcpy.da.UpdateCursor(catchments, fields) as rows:
            for row in rows:
                try:
                    print("Seg COMID {} has {} anadPres and {} dams downsteam".format(row[0], row[1], numDSDams[row[0]]))
                    if row[1] == 1 and numDSDams[row[0]] == 0:
                        row[2] = 10
                    else:
                        row[2] = 0
                    rows.updateRow(row)
                except:
                    print("unable to calculate DS dam count for COMID {}, setting to 0".format(mg.strOrigIDField))
                    row[2] = 0
                    rows.updateRow(row)


    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running anadromous presence metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def imperv(catchments, region):
    try:
        logger.info("Starting drainage area impervious metric...")
        # pull out streams/rivers from source NHDFlowlines
        streams = os.path.join(mg.metricsGDBFullPath, "NHDFlowline_AllStreams")

        # test to see if DA_PercImp is already calculated.  If it is, don't do it again.
        goAccumulate = 0
        if arcpy.Exists(streams):
            existField = arcpy.ListFields(streams, "DA_PercImp")
            if len(existField) >0:
                fields = ("DA_PercImp")
                vals = []
                with arcpy.da.UpdateCursor(streams, fields) as rows:
                    for row in rows:
                        vals.append(row[0])
                if None in vals:
                    goAccumulate = 1
                if min(vals) != 0:
                    goAccumulate =1
                if max(vals) > 110:
                    goAccumulate = 1 #possible to have some records end up ,ore than 100 due to funky cell alignment, but shoudln't happen
            else:
                goAccumulate = 1


        else:
            goAccumulate = 1

        if goAccumulate == 1:
            arcpy.Select_analysis(mg.nhdSourceFlowlines, streams, "FTYPE IN ('ArtificialPath', 'StreamRiver', 'Connector')")

            mg.dictJoin("plainJoin", True, catchments, mg.strOrigIDField, streams, mg.strOrigIDField, ("Ctch_OBJECTID",))
            mg.dictJoin("plainJoin", True, mg.nhdVAA, mg.strOrigIDField, streams, mg.strOrigIDField, ("UpHydroseq",))

            logger.info("...starting ZonalStats...")
            zonalStatsTable = os.path.join(mg.metricsGDBFullPath, "catchmentImprvStats_{}".format(region))
            arcpy.CheckOutExtension("Spatial")
            ZonalStatisticsAsTable(catchments, "OBJECTID", mg.imprv2016, zonalStatsTable)
            arcpy.CheckInExtension("Spatial")

            sumDict, countDict = accumulatePercImperv(streams, "flowline_geo", zonalStatsTable)


        mg.dictJoin("plainJoin", True, streams, mg.strOrigIDField, catchments, mg.strOrigIDField,("DA_PercImp",))

        ## Add back in coastal catchments that don't have an associated segment (due to dendrite)
        catchLyr = "catchLyr"
        arcpy.MakeFeatureLayer_management(catchments, catchLyr, "DA_PercImp is null")
        coastline = "coastline"
        arcpy.MakeFeatureLayer_management(mg.nhdSourceFlowlines, coastline, "FTYPE = 'Coastline'")
        arcpy.SelectLayerByLocation_management(catchLyr, "INTERSECT", coastline)
        fields =  ("Ctch_OBJECTID", "DA_PercImp")
        with arcpy.da.UpdateCursor(catchLyr, fields) as rows:
            for row in rows:
                row[1] = sumDict[row[0]]/countDict[row[0]]
                rows.updateRow(row)


        arcpy.AddField_management(catchments, "ImprvPoints", "SHORT")
        fields = ("DA_PercImp", "ImprvPoints")
        with arcpy.da.UpdateCursor(catchments, fields) as rows:
            for row in rows:
                if row[0] <=5:
                    row[1] = 10
                else:
                    row[1] = 0
                rows.updateRow(row)



    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running DA impervious metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def accumulatePercImperv(flowlines, geoFCName, zonalStatsTable):
    try:
        calculateMe = -999
        logger.info("...Prepping dendrite for accumulation...")
        sumDict = {}
        countDict = {}
        fields = ("OBJECTID_1", "SUM", "COUNT")
        with arcpy.da.SearchCursor(zonalStatsTable, fields) as rows:
            for row in rows:
                sumDict[row[0]] = row[1]
                countDict[row[0]] = row[2]

        arcpy.AddField_management(flowlines, "CtchImpSum", "DOUBLE")
        arcpy.AddField_management(flowlines, "CtchImpCount", "DOUBLE")
        fields = ("Ctch_OBJECTID", "CtchImpSum", "CtchImpCount")

        with arcpy.da.UpdateCursor(flowlines, fields) as rows:
            for row in rows:
                if row[0] in sumDict:
                    row[1] = sumDict[row[0]]
                    row[2] = countDict[row[0]]
                else:
                    row[1] = 0
                    row[2] = 0
                rows.updateRow(row)
        fields = arcpy.ListFields(flowlines)
        fieldNames =[]
        for field in fields:
            fieldNames.append(field.name)
        if "DA_ImpSum" not in fieldNames and "DA_ImpCount" not in fieldNames:
            arcpy.AddField_management(flowlines, "DA_ImpSum", "DOUBLE")
            arcpy.AddField_management(flowlines, "DA_ImpCount", "DOUBLE")
            fields = ("UpHydroseq","CtchImpSum", "DA_ImpSum", "CtchImpCount", "DA_ImpCount")
            with arcpy.da.UpdateCursor(flowlines, fields) as rows:
                for row in rows:
                    if row[0] == 0: #this is a headwater so DA == catch
                        row[2] = row[1]
                        row[4] = row[3]
                    else:
                        row[2] = -999
                        row[4] = -999
                    rows.updateRow(row)
        if arcpy.Exists(mg.geoNetFD):
            pass
        else:
            arcpy.CreateFeatureDataset_management(mg.metricsGDBFullPath, "Hydro", mg.nad83albers)
        geoFC =  os.path.join(mg.geoNetFD, geoFCName)
        if arcpy.Exists(geoFC):
            pass
        else:
            arcpy.CopyFeatures_management(flowlines, geoFC)
        if arcpy.Exists(mg.geoNet):
            pass
        else:
            arcpy.CreateGeometricNetwork_management(mg.geoNetFD, mg.geoNetName, [[geoFCName, "SIMPLE_EDGE", "NO"]])
            arcpy.SetFlowDirection_management(mg.geoNet, "WITH_DIGITIZED_DIRECTION")

        count = 0
        fields = ("DA_ImpCount",)
        with arcpy.da.SearchCursor(flowlines, fields) as rows:
            for row in rows:
                if row[0] == calculateMe:
                    count += 1
        logger.info("...Accumulating values for {} records".format(count))
        accumulate(mg.geoNet, geoFC, flowlines, calculateMe,  "CtchImpSum", "DA_ImpSum", "CtchImpCount", "DA_ImpCount")

        arcpy.AddField_management(flowlines, "DA_PercImp", "DOUBLE")
        fields = ("DA_ImpSum", "DA_ImpCount", "DA_PercImp")
        with arcpy.da.UpdateCursor(flowlines, fields) as rows:
            for row in rows:
                if row[1] >0:
                    row[2] = row[0]/row[1]
                else:
                    row[2] = 0
                rows.updateRow(row)

        return sumDict, countDict

    except Exception, e:
        arcpy.CheckInExtension("Spatial")
        tb = sys.exc_info()[2]
        msg ="Problem running accumulating impervious surface on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def pointSource(catchments):
    try:
        logger.info("Calculating point source metrics...")
        arcpy.AddField_management(catchments, "PtSourcePoints", "SHORT")
        mg.dictJoin("plainJoin", True, mg.streamCATPointSourceTbl,  mg.strOrigIDField, catchments, mg.strOrigIDField, ("TRIDensCat",))
        mg.replaceNumericalNulls(catchments, ["TRIDensCat", ])
        rankTierPoints(catchments, "TRIDensCat", "PtSourceRank", "A", "PtSourceTier", "PtSourcePoints", 5, 10)


    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running point source metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def nonPointSource(catchments, region):
    try:
        logger.info("Starting non-point source metric...")
        arcpy.CheckOutExtension("Spatial")

        arcpy.AddField_management(catchments, "PercNonPointLC", "DOUBLE")
        logger.info("...starting Tabulate Area...")
        tabAreaTable = os.path.join(mg.metricsGDBFullPath, "catchmentNLCD_{}".format(region))
        TabulateArea(catchments, "OBJECTID", mg.nlcd2016, "VALUE", tabAreaTable, 30)

        totalLCDict = {}
        nonPointLCDict =  {}
        fields = ("OBJECTID", "VALUE_11", "VALUE_21", "VALUE_22", "VALUE_23", "VALUE_24", "VALUE_31", "VALUE_41",
                  "VALUE_42", "VALUE_43", "VALUE_52", "VALUE_71", "VALUE_81", "VALUE_82", "VALUE_90", "VALUE_95")
        logger.info("...building dicts...")
        with arcpy.da.SearchCursor(tabAreaTable, fields) as rows:
            for row in rows:
                allVals = []
                nonPointSourceVals = []
                i=1
                nonPointSourceClasses = (2, 3, 12, 13)#dev open, low inten dev, past/hay, row crops
                while i <=15:
                    allVals.append(row[i])
                    if i in nonPointSourceClasses:
                        nonPointSourceVals.append(row[i])
                    i += 1

                totalArea = sum(allVals)
                totalNonPoint = sum(nonPointSourceVals)
                totalLCDict[row[0]] = totalArea
                nonPointLCDict[row[0]] = totalNonPoint

        fields = ("OBJECTID", "PercNonPointLC")
        with arcpy.da.UpdateCursor(catchments, fields) as rows:
            for row in rows:
                if totalLCDict[row[0]] >0:
                    row[1] = nonPointLCDict[row[0]]/totalLCDict[row[0]]
                else:
                    row[1] = 0
                rows.updateRow(row)

        arcpy.AddField_management(catchments, "nonPointSourcePoints", "SHORT")
        rankTierPoints(catchments, "PercNonPointLC", "NonPointRank", "A", "NonPointTier", "nonPointSourcePoints", 5, 10)

        arcpy.CheckInExtension("Spatial")

    except Exception, e:
        arcpy.CheckInExtension("Spatial")
        tb = sys.exc_info()[2]
        msg ="Problem running non-point source metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def riparianBuffer(catchments, region):
    try:
        logger.info("Starting riparian buffer...")
        arcpy.CheckOutExtension("Spatial")

        arcpy.AddField_management(catchments, "PercARANatural", "DOUBLE")

        logger.info("...starting raster intersect...")
        ### arcpy.Intersect_analysis([catchments, mg.ara], catchmentARA, "ALL")  #too big, doesn't work, do in raster world instead
        catchments_gr = os.path.join(mg.metricsGDBFullPath, "catchments_gr_{}".format(region))
        arcpy.env.snapRaster = mg.nlcd2016
        logger.info("...converting catchments to raster...")
        arcpy.PolygonToRaster_conversion(catchments, "OBJECTID", catchments_gr, "CELL_CENTER", "", 30)
        logger.info("...Intersecting catchments and ARA (Con)...")
        catchARA_gr = Con(mg.ara_gr, catchments_gr)
        catchmentARA = os.path.join(mg.metricsGDBFullPath, "catchmentARA_{}".format(region))
        catchARA_gr.save(catchmentARA)


        logger.info("...running tabulate area...")
        tabAreaTable = os.path.join(mg.metricsGDBFullPath, "catchmentARA_NLCD_{}".format(region))
        TabulateArea(catchmentARA, "VALUE", mg.nlcd2016, "VALUE", tabAreaTable, 30)

        totalLCDict = {}
        araNatLCDict = {}
        fields = ("VALUE", "VALUE_11", "VALUE_21", "VALUE_22", "VALUE_23", "VALUE_24", "VALUE_31", "VALUE_41",  #here, the first "VALUE" is the OBJECTID of the vector catchemnts
                  "VALUE_42", "VALUE_43", "VALUE_52", "VALUE_71", "VALUE_81", "VALUE_82", "VALUE_90", "VALUE_95")
        with arcpy.da.SearchCursor(tabAreaTable, fields) as rows:
            for row in rows:
                allVals = []
                araNatVals = []
                i=1
                naturalClasses = (1, 6, 7, 8, 9, 10, 11, 14, 15) #water, all forest, barren, herb, scrub/shrub, wetlands
                while i <=15:
                    allVals.append(row[i])
                    if i in naturalClasses:
                        araNatVals.append(row[i])
                    i += 1

                totalArea = sum(allVals)
                totalARANat = sum(araNatVals)
                totalLCDict[row[0]] = totalArea
                araNatLCDict[row[0]] = totalARANat
        fields = ("OBJECTID", "PercARANatural")
        with arcpy.da.UpdateCursor(catchments, fields) as rows:
            for row in rows:
                try:
                    row[1] = araNatLCDict[row[0]]/totalLCDict[row[0]]
                except:
                    row[1] = 0
                rows.updateRow(row)

        arcpy.AddField_management(catchments, "araNaturalPoints", "SHORT")
        rankTierPoints(catchments, "PercARANatural", "araNatRank", "D", "araNatTier", "araNaturalPoints", 5, 10)

        arcpy.CheckInExtension("Spatial")

    except Exception, e:
        arcpy.CheckInExtension("Spatial")
        tb = sys.exc_info()[2]
        msg ="Problem running riparian metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def esaCriticalHabitat(catchments):
    try:
        logger.info("Starting ESA critical habitat...")
        arcpy.AddField_management(catchments, "esaPoints", "SHORT")
        arcpy.CalculateField_management(catchments, "esaPoints", 0, "PYTHON")
        ctchLyr = "catchmentsLayer"
        arcpy.MakeFeatureLayer_management(catchments, ctchLyr)
        arcpy.SelectLayerByLocation_management(ctchLyr, "INTERSECT", mg.sturgCritHab, 0, "NEW_SELECTION")
        arcpy.SelectLayerByLocation_management(ctchLyr, "INTERSECT", mg.salmCritHab, 0, "ADD_TO_SELECTION")
        arcpy.CalculateField_management(ctchLyr, "esaPoints", 10, "PYTHON")
        arcpy.SelectLayerByAttribute_management(ctchLyr, "CLEAR_SELECTION")

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running ESA Critical Habitat metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def flowAlteration(catchments):
    try:
        logger.info("Starting flow alteration...")
        mg.dictJoin("plainJoin", True, mg.streamCATDamsFlowAlt,  mg.strOrigIDField, catchments, mg.strOrigIDField, ("DamNIDStorWs",))
        mg.replaceNumericalNulls(catchments, ["DamNIDStorWs",])
        arcpy.AddField_management(catchments, "flowAltPoints", "SHORT")
        rankTierPoints(catchments, "DamNIDStorWs", "flowAltRank", "A", "flowAltTier", "flowAltPoints", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running flow altration metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def fragmentation(catchments, region):
    try:
        logger.info("Starting local fragmentation...")
        arcpy.AddField_management(catchments, "barrDensity", "DOUBLE")
        localFrags =  "in_memory/localFragmentors_{}".format(region)
        arcpy.Select_analysis(mg.regionalBarriers, localFrags, "Use >0 and Type <>'Natural Barrier'")
        ctchBarriers = "in_memory/catchmentBarriers_{}".format(region)
        arcpy.SpatialJoin_analysis(catchments, mg.regionalBarriers, ctchBarriers)
        densityDict = {}
        fields =(mg.strOrigIDField, "Join_Count", "AreaSqKM")
        with arcpy.da.SearchCursor(ctchBarriers, fields) as rows:
            for row in rows:
                densityDict[row[0]] = row[1]/row[2]

        fields  = (mg.strOrigIDField, "barrDensity")
        with arcpy.da.UpdateCursor(catchments, fields) as rows:
            for row in rows:
                row[1] = densityDict[row[0]]
                rows.updateRow(row)

        arcpy.AddField_management(catchments, "fragmentPoints", "SHORT")
        rankTierPoints(catchments, "barrDensity", "fragmentRank", "A", "fragmentTier", "fragmentPoints", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg ="Problem running fragmentation metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()



#########  Estuarine #####################
def savOys(hexagons, region):
    try:
        logger.info("Starting SAV/Oyster metric...")
        polysInHexagons(region, hexagons, [mg.sav, mg.oysterReefMussel, mg.cmec_oysters, mg.delawareBayOyster, mg.rutgersNJOys, mg.vosaraOysters], "savOys", "D", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running sav/oyster metric on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def wetlands(hexagons, region):
    try:
        logger.info("Starting wetlands metric...")
        logger.info("...pulling out estuarine marsh from NWI...")
        arcpy.env.workspace = mg.metricsGDBFullPath
        estuarineWetlands = os.path.join(mg.metricsGDBFullPath, "NWI_Estuarine")
        estuarineWetlandDisso = os.path.join(mg.metricsGDBFullPath, "NWI_EstuarineDisso")
        if arcpy.Exists(estuarineWetlandDisso) == False:
            arcpy.Select_analysis(mg.nwi, estuarineWetlands,
                                  "{}".format(mg.estuarineWetlandSQL))  # E2 == estuarine intertidal
            logger.info("Dissolving wetlands...")
            arcpy.Dissolve_management(in_features=estuarineWetlands, out_feature_class=estuarineWetlandDisso,
                                      dissolve_field="WETLAND_TYPE",
                                      multi_part="SINGLE_PART")
        polysInHexagons(region, hexagons, [estuarineWetlandDisso,], "wetlands", "D", 5, 10)  #wetlands

        logger.info("...finished estuarine wetlands metric ...")

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running estuarine wetlands metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def waterVegEdge(hexagons, region):
    try:
        logger.info("Starting water-vegetation edge metric...")
        arcpy.env.workspace = mg.metricsGDBFullPath
        estuarineWetlandEdge = os.path.join(mg.metricsGDBFullPath, "NWI_EstuarineEdge")
        estuarineWetlands = os.path.join(mg.metricsGDBFullPath, "NWI_Estuarine")
        estuarineWetlandDisso = os.path.join(mg.metricsGDBFullPath, "NWI_EstuarineDisso")
        if arcpy.Exists(estuarineWetlandDisso) == False:
            logger.info("...pulling out estuarine marsh from NWI...")
            arcpy.Select_analysis(mg.nwi, estuarineWetlands,
                                  "{}".format(mg.estuarineWetlandSQL))  # E2 == estuarine intertidal
            logger.info("Dissolving wetlands...")
            arcpy.Dissolve_management(in_features=estuarineWetlands, out_feature_class=estuarineWetlandDisso,
                                      dissolve_field="WETLAND_TYPE", statistics_fields="",
                                      multi_part="SINGLE_PART", unsplit_lines="DISSOLVE_LINES")
            logger.info("...pulling out estuarine marsh edge from NWI...")

        else:
            logger.info("...Estuarine marsh layer already exists.  Pulling out estuarine marsh edge...")

        arcpy.PolygonToLine_management(estuarineWetlandDisso, estuarineWetlandEdge)

        linearLengthInHexagon(region, hexagons, [estuarineWetlandEdge,], "estWetEdge", "D", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running water veg edge metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def protectedArea(hexagons, region):
    try:
        logger.info("Starting distance to protected area...")
        protectedNearTable = os.path.join(mg.metricsGDBFullPath, "protectedNearTable_{}".format(region))
        arcpy.GenerateNearTable_analysis(hexagons, mg.protectedAreas, protectedNearTable)
        arcpy.AddField_management(protectedNearTable, "protectedDist", "DOUBLE")
        arcpy.CalculateField_management(protectedNearTable, "protectedDist", "!NEAR_DIST!", "PYTHON")
        mg.dictJoin("plainJoin", True, protectedNearTable, "IN_FID", hexagons, "OBJECTID", ["protectedDist",])
        arcpy.AddField_management(hexagons, "protectedDistPoints", "SHORT")

        fields = ("protectedDist", "protectedDistPoints")
        with arcpy.da.UpdateCursor(hexagons, fields) as rows:
            for row in rows:
                if row[0] <=500:
                    row[1] = 10
                else:
                    row[1] = 0
                rows.updateRow(row)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem protected area metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def devDistance(hexagons, region):
    try:
        logger.info("Starting distance to development metric...")
        portsNearTable = os.path.join(mg.metricsGDBFullPath, "portsNearTable_{}".format(region))
        arcpy.GenerateNearTable_analysis(hexagons, mg.ports, portsNearTable)
        arcpy.AddField_management(portsNearTable, "portDist", "DOUBLE")
        arcpy.CalculateField_management(portsNearTable, "portDist", "!NEAR_DIST!", "PYTHON")
        mg.dictJoin("plainJoin", True, portsNearTable, "IN_FID", hexagons, "OBJECTID", ["portDist",])
        arcpy.AddField_management(hexagons, "portDistPoints", "SHORT")
        rankTierPoints(hexagons, "portDist", "portDistRank", "D", "portDistTier", "portDistPoints", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running distance to development metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def waterQuality(hexagons):
    try:
        logger.info("Starting water quality metric...")
        arcpy.env.outputCoordinateSystem = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\Scripts\NAD_1983_Albers.prj"
        polys303d = os.path.join(mg.metricsGDBFullPath, "waterQaulity_303d_use")
        arcpy.Select_analysis(mg.water303dPolys, polys303d, "LW_DETAILED_CAUSE_NAME NOT IN ('FECAL COLIFORM')")

        arcpy.AddField_management(hexagons, "waterQual303d", "SHORT")
        arcpy.AddField_management(hexagons, "waterQual303dPoints", "SHORT")
        hexLyr = "hexLyr"
        arcpy.MakeFeatureLayer_management(hexagons, hexLyr)
        arcpy.SelectLayerByLocation_management(hexLyr, "INTERSECT", polys303d, "", "NEW_SELECTION")
        arcpy.CalculateField_management(hexLyr, "waterQual303d", 1, "PYTHON")
        arcpy.SelectLayerByAttribute_management(hexLyr, "SWITCH_SELECTION")
        arcpy.CalculateField_management(hexLyr, "waterQual303d", 0, "PYTHON")
        fields = ("waterQual303d", "waterQual303dPoints")
        with arcpy.da.UpdateCursor(hexagons, fields) as rows:
            for row in rows:
                if row[0] ==0:
                    row[1] = 10
                else:
                    row[1] = 0
                rows.updateRow(row)


    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running water quality metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def hardShore(hexagons, region):
    try:
        logger.info("Starting hardened shoreline metric...")
        logger.info("...pulling out hardened shoreline from NOAA ESI...")
        hardenedShore = os.path.join(mg.metricsGDBFullPath, "hardenedShore")
        arcpy.env.outputCoordinateSystem = r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\Scripts\NAD_1983_Albers.prj"
        arcpy.Select_analysis(mg.noaaESI, hardenedShore, "GENERALIZED_ESI_TYPE LIKE '%1%'")

        linearLengthInHexagon(region, hexagons, [hardenedShore,], "hardShore", "A", 5, 10)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running hardened shoreline metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def habitatFragmentation(hexagons, region):
    try:
        logger.info("Starting estuarine habitat fragmentation metric...")
        logger.info("...identifying causeways...")
        causeways = os.path.join(mg.metricsGDBFullPath, "Estuarine_Marsh_Causeways")
        arcpy.Intersect_analysis([mg.roads, mg.nwi_estuarine_agg], causeways)
        linearLengthInHexagon(region, hexagons, [causeways, ], "causeway", "A", 1, 10)
        ## overwrite rank and points so only those with 0 causeway get points (Tier 1 will include those with a small amount of causeway)
        arcpy.CalculateField_management(hexagons, "causewayPoints", 0, "PYTHON")
        arcpy.DeleteField_management(hexagons, ["causewayRank", "causewayTier"])
        fields = ("causewayLength", "causewayPoints")
        with arcpy.da.UpdateCursor(hexagons, fields) as rows:
            for row in rows:
                if row[0] ==0:
                    row[1] = 10
                else:
                    row[1] = 0
                rows.updateRow(row)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running habitat fragmentation metrics on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()



def countDS(barriers,  barrUID, barrUSNetID, barrDSNetID):
    try:
        logger.info("Calculating downstream barrier count...")
        countStart = time.time()
        arcpy.AddField_management(barriers, "batCountDS", "SHORT")
        arcpy.CalculateField_management(barriers, "batCountDS", 0, "PYTHON")

        #populate a dict with the network IDs
        netIDDict = {}
        fields = (barrUID, barrUSNetID, barrDSNetID)
        print("...populating network ID dict...")
        with arcpy.da.SearchCursor(barriers, fields) as rows:
            for row in rows:
                netIDDict[row[0]]= [row[1], row[2]]

        fields = (barrUID, "batCountDS")
        with arcpy.da.UpdateCursor(barriers, fields) as rows:
            for row in rows:
                print("...counting DS IDs for barrier {}...".format(row[0]))
                dsIDs = []
                getDSids(row[0], netIDDict, dsIDs)
                numDSBarrs = len(dsIDs)
                row[1] = numDSBarrs
                rows.updateRow(row)
        countEnd = time.time()
        countDur = countEnd-countStart
        logger.info("Successfully finished counting downstream barriers in {} seconds...".format(countDur))
    except Exception as e:
        tb = sys.exc_info()[2]
        msg = "Problem counting downstream barriers on StatewideMetrics line {}. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def getDSids(startID, myDict, ids, stop=None):
    """
    function to find all the downstream ids of a barrier by traversing the
    batUSNetID & batDSNetID
    startID: the barrier for which all downstream barriers are being found
    myDict: a dictionary of the barrier table where myDict["UNIQUE_ID"] = (batUSNetID, batDSNetID)
    ids = an empty list that will be populated with all of the downstream IDs
    """
    try:
        for key, value in myDict.iteritems():
            if value[0] == myDict[startID][1] and str(key) != stop:
                ids.append(key)
                return(getDSids(key, myDict, ids))
            if str(key) == stop:
                break
        return ids


    except Exception as e:
        tb = sys.exc_info()[2]
        print ("Problem getting downstream IDs on line {} at {}".format(tb.tb_lineno, stamp()))
        print(str(e))


def polysInHexagons(region, hexagons, polyList, nameAbbrv, sortOrder, numTiers, numPoints):
    try:
        """
        polyList: a list of polygon feature classes that will be merged together.  THe total area of these polygons in aech hexagon will be calculated
        nameAbbrv: string. a short name that will be used for fields and intermediate feature classes.  e.g. "savOys"
        numTiers: the number of 5% Tiers that will be assigned points.  e.g. 5 tiers if the top 25% will get points
        numPoints: the number of points taht will be assigend to those tiers
        """
        logger.info("...starting poly area in hexagon metric for {}...".format(nameAbbrv))

        #delete old fields before intersecting, or they persist
        delFields = ("{}Area".format(nameAbbrv), "{}Points".format(nameAbbrv), "{}Rank".format(nameAbbrv), "{}Tier".format(nameAbbrv))
        for field in delFields:
            try:
                arcpy.DeleteField_management(hexagons, field)
            except:
                pass

        hexagonAreaDict = {}
        fields = ("GRID_ID", "Shape_Area")
        with arcpy.da.SearchCursor(hexagons, fields) as rows:
            for row in rows:
                hexagonAreaDict[row[0]] = row[1]

        if len(polyList) > 1:

            unioned = os.path.join(mg.metricsGDBFullPath, "{}Union_{}".format(nameAbbrv, region))
            dissolved = os.path.join(mg.metricsGDBFullPath, "{}Disso_{}".format(nameAbbrv, region))
            arcpy.Union_analysis(polyList, unioned)
            arcpy.Dissolve_management(in_features=unioned, out_feature_class=dissolved, multi_part="SINGLE_PART")
        elif len(polyList) == 1:
            dissolved = polyList[0]
        else:
            logger.error("There was a problem merging the polygon layers. Length of feature list...")
            sys.exit()
        arcpy.DeleteField_management(dissolved, ["GRID_ID", "GRID_ID_1"])
        intersectedHexagons =  os.path.join(mg.metricsGDBFullPath, "{}Hexagons_{}".format(nameAbbrv, region))
        arcpy.Intersect_analysis([dissolved, hexagons], intersectedHexagons)

        fields = ("GRID_ID", "Shape_Area")
        featAreaDict = defaultdict(list)
        with arcpy.da.SearchCursor(intersectedHexagons, fields) as rows:
            for row in rows:
                print("{}={}".format(row[0], row[1]))
                try:
                    featAreaDict[row[0]].append(row[1]) #there are some hexagons with multiple sav/oys polys, so add to list and sum
                except:
                    featAreaDict[row[0]] = 0


        arcpy.AddField_management(hexagons, "{}Area".format(nameAbbrv), "DOUBLE")
        fields = ("GRID_ID", "{}Area".format(nameAbbrv))
        with arcpy.da.UpdateCursor(hexagons, fields) as rows:
            for row in rows:
                try:
                    row[1] = sum(featAreaDict[row[0]])/hexagonAreaDict[row[0]]
                except:
                    row[1] = 0
                rows.updateRow(row)

        arcpy.AddField_management(hexagons, "{}Points".format(nameAbbrv), "SHORT")
        rankTierPoints(hexagons, "{}Area".format(nameAbbrv), "{}Rank".format(nameAbbrv), sortOrder, "{}Tier".format(nameAbbrv), "{}Points".format(nameAbbrv), numTiers, numPoints)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running poly area in hexagon metric for {} on line {} of Metrics. {}".format(nameAbbrv, tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def linearLengthInHexagon(region, hexagons, linearFeatList, nameAbbrv, sortOrder, numTiers, numPoints):
    try:
        """
        linearFeatList: a list of line feature classes that will be merged together.  THe total length of these lines in each hexagon will be calculated
        nameAbbrv: string. a short name that will be used for fields and intermediate feature classes.  e.g. "savOys"
        numTiers: the number of 5% Tiers that will be assigned points.  e.g. 5 tiers if the top 25% will get points
        numPoints: the number of points taht will be assigend to those tiers
        """
        logger.info("...starting linear feature length in hexagon metric for {}...".format(nameAbbrv))

        #delete old fields before intersecting, or they persist
        delFields = ("{}Length".format(nameAbbrv), "{}Points".format(nameAbbrv), "{}Rank".format(nameAbbrv), "{}Tier".format(nameAbbrv))
        for field in delFields:
            try:
                arcpy.DeleteField_management(hexagons, field)
            except:
                pass


        if len(linearFeatList) > 1:
            merged = os.path.join(mg.metricsGDBFullPath, "{}Merge_{}".format(nameAbbrv, region))
            arcpy.Merge_management(linearFeatList, merged)
        elif len(linearFeatList) == 1:
            merged = linearFeatList[0]
        else:
            logger.error("There was a problem merging the line layers.  Length of feature list...")
            sys.exit()

        intersectedHexagons =  os.path.join(mg.metricsGDBFullPath, "{}Hexagons_{}".format(nameAbbrv, region))
        logger.info("...intersecting...")
        arcpy.Intersect_analysis([merged, hexagons], intersectedHexagons)

        featLengthDict = defaultdict(list)
        fields =  ("GRID_ID", "Shape_Length")
        with arcpy.da.SearchCursor(intersectedHexagons, fields) as rows:
            for row in rows:
                try:
                    featLengthDict[row[0]].append(row[1]) #there are some hexagons with multiple features, so add to list and sum
                except:
                    featLengthDict[row[0]] = 0


        arcpy.AddField_management(hexagons, "{}Length".format(nameAbbrv), "DOUBLE")
        fields = ("GRID_ID", "{}Length".format(nameAbbrv))
        with arcpy.da.UpdateCursor(hexagons, fields) as rows:
            for row in rows:
                try:
                    row[1] = sum(featLengthDict[row[0]])
                except:
                    row[1] = 0
                rows.updateRow(row)

        arcpy.AddField_management(hexagons, "{}Points".format(nameAbbrv), "SHORT")
        rankTierPoints(hexagons, "{}Length".format(nameAbbrv), "{}Rank".format(nameAbbrv), sortOrder, "{}Tier".format(nameAbbrv),
                       "{}Points".format(nameAbbrv), numTiers, numPoints)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem running linear feature metrics for {} on line {} of Metrics. {}".format(nameAbbrv, tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def rankTierPoints(fc, valField, rankField, sortOrder, tierField,  pointField, tiersWithPoints, points):
    arcpy.AddField_management(fc, rankField, "LONG")
    arcpy.AddField_management(fc, tierField, "SHORT")
    PYM.myRank(fc, valField, rankField, sortOrder)
    TM.tier(fc, rankField, tierField)

    fields = (tierField, pointField)
    with arcpy.da.UpdateCursor(fc, fields) as rows:
        for row in rows:
            if row[0] <= tiersWithPoints:
                row[1] = points
            else:
                row[1] = 0
            rows.updateRow(row)

def totalPoints(fc):
    try:
        try:
            arcpy.DeleteField_management(fc, "TotalPoints")
        except:
            pass

        fields = arcpy.ListFields(fc)
        pointsFields = []
        for field in fields:
            if "Points" in field.name:
                pointsFields.append((field.name))
        arcpy.AddField_management(fc, "TotalPoints", "SHORT")
        pointsFields.append("TotalPoints")

        pointsFields =[x.encode('UTF8') for x in pointsFields]
        print pointsFields
        with arcpy.da.UpdateCursor(fc, pointsFields) as rows:
            for row in rows:
                i = 0
                points = []
                while i <8:
                    points.append(row[i])
                    i+=1
                row[8]=sum(points)
                rows.updateRow(row)

    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem calculating total points on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()


def makeMapServiceLayers(fc, mapServGDB):
    try:
        fcName = fc.split("\\")[-1]
        logger.info("Making map service layers for {}...".format(fcName))
        mapServiceLayer = os.path.join(mapServGDB, fcName)
        if arcpy.Exists(mapServiceLayer):
            print("deleting")
            arcpy.Delete_management(mapServiceLayer)
        arcpy.Project_management(fc, mapServiceLayer, r"K:\ACFHP_ScienceData\NEDiadromousHabitatMapping\GIS\Scripts\WebMerc.prj" )
    except Exception, e:
        tb = sys.exc_info()[2]
        msg = "Problem making map service layers on line {} of Metrics. {}".format(tb.tb_lineno, e)
        logger.error(msg)
        sys.exit()

def accumulate(network, netHydroFC_path, nonNetHydroFC, calculateMe, accumSourceField1, accumTargetField1, accumSourceField2=None, accumTargetField2=None, accumSourceField3=None, accumTargetField3=None, accumSourceField4=None, accumTargetField4=None, accumSourceField5=None, accumTargetField5=None, accumSourceField6=None, accumTargetField6=None):
    try:
        arcpy.env.workspace = "in_memory"

        fields = ("OBJECTID", accumSourceField1, accumTargetField1)
        numFields = 1
        if accumSourceField2 is not None:
            fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2)
            numFields = 2
        if accumSourceField3 is not None:
            fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2, accumSourceField3, accumTargetField3)
            numFields = 3
        if accumSourceField4 is not None:
            fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2, accumSourceField3, accumTargetField3, accumSourceField4, accumTargetField4)
            numFields = 4
        if accumSourceField5 is not None:
            fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2, accumSourceField3, accumTargetField3, accumSourceField4, accumTargetField4, accumSourceField5, accumTargetField5)
            numFields = 5
        if accumSourceField6 is not None:
            fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2, accumSourceField3, accumTargetField3, accumSourceField4, accumTargetField4, accumSourceField5, accumTargetField5, accumSourceField6, accumTargetField6)
            numFields = 6

        #get the text name of the network FC without the full path by taking what's after the last "\"
        netHydroFC = netHydroFC_path.split("\\")[-1].strip()

        #list fields to include in cursor
        ##fields = ("OBJECTID", accumSourceField1, accumTargetField1, accumSourceField2, accumTargetField2, accumSourceField3, accumTargetField3)
        arcpy.AddMessage("Running...")
        #open arcpy.da cursor
        with arcpy.da.UpdateCursor(nonNetHydroFC, fields) as rows:
            arcpy.AddMessage(fields)
            print(fields)
            for row in rows:
                #get values for each row
                rowObjID = row[0]

                #if there are Nulls in the source field, treat them as 0s, otherwise use value
                if row[1] is None:
                    rowCtchVal1 = 0
                else:
                    rowCtchVal1 = float(row[1])
                DAval1 = float(row[2])
                if numFields >1:
                    if row[3] is None:
                        rowCtchVal2 = 0
                    else:
                        rowCtchVal2 = float(row[3])
                if numFields >2:
                    if row[5] is None:
                        rowCtchVal3 = 0
                    else:
                        rowCtchVal3 = float(row[5])
                if numFields >3:
                    if row[7] is None:
                        rowCtchVal4 = 0
                    else:
                        rowCtchVal4 = float(row[7])
                if numFields >4:
                    if row[9] is None:
                        rowCtchVal5 = 0
                    else:
                        rowCtchVal5 = float(row[9])
                if numFields >5:
                    if row[11] is None:
                        rowCtchVal6 = 0
                    else:
                        rowCtchVal6 = float(row[11])

                #If there's already an accumulated value skip that record
                if DAval1 != int(calculateMe):
                    arcpy.AddMessage("ObjectID " + str(rowObjID) + " is already calculated")

                #If the value is equal to the "calculate me" flag run the operation
                if DAval1 == int(calculateMe):

                    start = time.time()
                    #make a feature layer in memory and select the record that is active in the cursor
                    arcpy.MakeFeatureLayer_management(nonNetHydroFC, "sel_lyr")
                    selection = '"OBJECTID" = {}'.format(rowObjID)
                    arcpy.SelectLayerByAttribute_management("sel_lyr", "NEW_SELECTION", selection)

                    #create a point at the start vertex of the selected record
                    arcpy.FeatureVerticesToPoints_management("sel_lyr", "flag", "START")

                    #select the upstream network & take the line layer from the returned layer group (network + junctions)
                    flag = "flag"
                    arcpy.TraceGeometricNetwork_management(network, "netLayer", flag, "TRACE_UPSTREAM")
                    usSelection = arcpy.SelectData_management("netLayer", netHydroFC)

                    #sum first field
                    field = accumSourceField1
                    usVals1 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                    sumUSVals1 = float(sum(usVals1))
                    newDAVal1 = float(sumUSVals1 + rowCtchVal1)
                    row[2] = newDAVal1

                    #if selected, sum 2nd field
                    if numFields >= 2:
                        field = accumSourceField2
                        usVals2 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                        sumUSVals2 = float(sum(usVals2))
                        newDAVal2 = float(sumUSVals2 + rowCtchVal2)
                        row[4] = newDAVal2

                    #if selected, sum 3rd field
                    if numFields >= 3:
                        field = accumSourceField3
                        usVals3 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                        sumUSVals3 = float(sum(usVals3))
                        newDAVal3 = float(sumUSVals3 + rowCtchVal3)
                        row[6] = newDAVal3

                    #if selected, sum 4th field
                    if numFields >= 4:
                        field = accumSourceField4
                        usVals4 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                        sumUSVals4 = float(sum(usVals4))
                        newDAVal4 = float(sumUSVals4 + rowCtchVal4)
                        row[8] = newDAVal4

                    #if selected, sum 5th field
                    if numFields >= 5:
                        field = accumSourceField5
                        usVals5 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                        sumUSVals5 = float(sum(usVals5))
                        newDAVal5 = float(sumUSVals5 + rowCtchVal5)
                        row[10] = newDAVal5

                    #if selected, sum 6th field
                    if numFields == 6:
                        field = accumSourceField6
                        usVals6 = [r[0] for r in arcpy.da.SearchCursor(usSelection, (field))]
                        sumUSVals6 = float(sum(usVals6))
                        newDAVal6 = float(sumUSVals6 + rowCtchVal6)
                        row[12] = newDAVal6

                    end = time.time()
                    duration = end-start
                    duration = round(duration, 2)
                    arcpy.AddMessage("Finished ObjectID# {} in {} seconds.".format(rowObjID, duration))
                    print("Finished ObjectID# {} in {} seconds.".format(rowObjID, duration))

                rows.updateRow(row)
        arcpy.env.workspace = workspace
    except Exception, e:
        tb = sys.exc_info()[2]
        logger.error("Problem accumulating values on line {}. {}.".format(tb.tb_lineno, e.message))
        sys.exit()


def stamp():
    myNow = str(datetime.datetime.now()).split('.')[0]
    return myNow



if __name__ == '__main__':
    main()