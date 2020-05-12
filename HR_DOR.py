#-------------------------------------------------------------------------------
# Name:        HR_DOR
# Purpose:      Assigns network IDs based on connected river segments defined by
#               dams (or other barriers).
# Author:      This script was adapted by Erik Martin (emartin@tnc.org), with
#              permission, from a portion of the HydroRout scripts developed by
#              Guenther Grill at McGill University
#              (https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.9740)
#-------------------------------------------------------------------------------

from collections import defaultdict
import sys, os, myGlobals
logger = myGlobals.rootLogger



try:
    arcpy
except NameError:
    import arcpy
import numpy as np

Segment_dict = {}

def globals(st, dt, og, hrNOID, hrNDOID, hrNUOID, exp):
    logger.info("HR globals func")
    global exportFiles
    exportFiles = exp

    global stream_table, dam_table, output_gdb
    stream_table = st
    dam_table = dt
    output_gdb = og

    # Globals for required stream fields
    global DOR, SEGID,  LEN_DOWN, LEN_UP, GOID, NOID, NDOID, NUOID

    SEGID = myGlobals.networkIDField #"NETWORK_ID"
    LEN_DOWN = "LENGTH_DOWN_KM"
    LEN_UP = "LENGTH_UP_KM"
    VOL_UP = "VOLUME_UP_TCM"
    GOID = "GOID"
    NOID = hrNOID
    NDOID = hrNDOID
    NUOID = hrNUOID

   # global year_thresh
   # year_thresh = 2040

def run(st, dt, og, hrNOID, hrNDOID, hrNUOID,  barrID, exp, stream_fields):
    try:
        logger.info("HR run func")
        globals(st, dt, og, hrNOID, hrNDOID, hrNUOID, exp)

        streams = load_streams(stream_fields)

        dams = load_dams(barrID, hrNOID)

        get_upstream_segments(dams, streams)

        outtbl = export(streams, output_gdb)

        return outtbl, streams

    except Exception as e:
        import traceback, sys
        tb = sys.exc_info()[2]
        arcpy.AddError("There was a problem running the HbD platform.  Failed on HR line {}. ".format(tb.tb_lineno) + e.message)
        print("There was a problem running the HbD platform.  Failed on HR line {}. ".format(tb.tb_lineno) + e.message)
        sys.exit()


def load_streams(stream_fields):
    logger.info("HR load streams")
    whereBClause = ""
    arr = arcpy.da.TableToNumPyArray(stream_table, stream_fields, whereBClause, null_value=0)

    arr = add_fields(arr, [(SEGID, 'u4')])
    arr[SEGID] = 0

    return arr

def load_dams(barrID, hrNOID):
    logger.info("HR load dams")
    flds = [barrID, hrNOID]
    dams = arcpy.da.TableToNumPyArray(dam_table, flds, "", null_value=0)

    return dams


def get_upstream_segments(dams, streams):  # List of OIDs
    logger.info("HR get us segs")
    seg = 0
    dam_list = get_oid_list(dams)
    nodes = []
    stop = set([])
    [stop.add(a) for a in dam_list]

    for dam in dam_list:
        nodes.append(dam)  # Add the dam to the nodes list to process
        stop.remove(dam)  # remove the same dam from the stop list to not stop the routing
        seg += 1

        try:
            while 1:
                new_nodes = []
                if len(nodes) == 0:
                    break
                for node in nodes:
                    if node != -1 and node != '':
                        if streams[node - 1][NOID] not in stop:
                            # update segment
                            streams[node - 1][SEGID] = seg

                            ups = streams[node - 1][NUOID].split("_")
                            if len(ups) > 0:
                                for up in ups:
                                    if up != '':
                                        new_nodes.append(int(up))
                nodes = new_nodes

            # Add the dam back to the stop list after processing
            stop.add(dam)

        except Exception as e:
            tb = sys.exc_info()[2]
            arcpy.AddError("There was a problem running the HbD platform.  Failed on HR line {}. ".format(tb.tb_lineno) + e.message)
            print("There was a problem running the HbD platform.  Failed on HR line {}. ".format(tb.tb_lineno) + e.message)
            sys.exit()


def get_oid_list(dams):
    logger.info("HR get OID list")
    list = []
    # Sort the dams by year
    # np.sort(dams, order='Year')

    for dam in dams:
        list.append(dam[NOID])
    return list

def add_fields(array, desc):
    logger.info("HR add fields")
    if array.dtype.fields is None:
        print("A must be a structured numpy array")
    b = np.empty(array.shape, dtype=array.dtype.descr + desc)

    for name in array.dtype.names:
        b[name] = array[name]
    return b


def export(streams,  out_gdb):
    logger.info("HR export")
    out_tbl = out_gdb + "\HR_out_table"
    if exportFiles == 1:
        if arcpy.Exists(out_tbl):
            arcpy.Delete_management(out_tbl)
        arcpy.da.NumPyArrayToTable(streams, out_tbl)
    return out_tbl