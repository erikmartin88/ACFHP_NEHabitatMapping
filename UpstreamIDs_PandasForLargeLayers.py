#-------------------------------------------------------------------------------
# Name:        Get Upstream IDs.  Uses Pandas python package
#               For large layers (millions of records) run in 64-bit python
#
# Author:      emartin
#
# Created:     13/02/2017
# Copyright:   (c) emartin 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
import pandas as pd
import sys
from time import strftime
import time
from collections import defaultdict
import numpy as np
from operator import itemgetter

def makeIDs(streamFC, segIDField, usSegIDField, dsSegIDField, fnodeField, tnodeField):
    try:
##        print("Starting Pandas at {}".format(strftime("%H:%M:%S")))
        fields = (segIDField, fnodeField, tnodeField)
        arr = arcpy.da.TableToNumPyArray(streamFC, fields)
        df = pd.DataFrame(arr)
        df2 = df
        #Join the dataframes -- analogous to a regular database join
        joinedDF = pd.merge(df, df2, left_on=fnodeField, right_on=tnodeField)
        usIDsDict = defaultdict(list)
        for index, row in joinedDF.iterrows():
            usIDsDict[int(row['{}_x'.format(segIDField)])].append(int(row['{}_y'.format(segIDField)]))

        joinedDF = pd.merge(df, df2, left_on=tnodeField, right_on=fnodeField)
        dsIDsDict = {}
        for index, row in joinedDF.iterrows():
            dsIDsDict[int(row['{}_x'.format(segIDField)])] = int(row['{}_y'.format(segIDField)])


##        print("Finished Pandas at {}".format(strftime("%H:%M:%S")))
##        print("Starting update cursor at {}".format(strftime("%H:%M:%S")))
        fields = (segIDField, usSegIDField, dsSegIDField)
        with arcpy.da.UpdateCursor(streamFC, fields) as rows:
            for row in rows:
                row[1] = str(usIDsDict[row[0]]).replace(",", "_").replace("[", "").replace("]", "").replace(" ", "")
                try:
                    row[2] = dsIDsDict[row[0]]
                except:
                    row[2] = None
                rows.updateRow(row)
##        print("Finished update cursor at {}".format(strftime("%H:%M:%S")))

    except Exception as e:
        tb = sys.exc_info()[2]
        print(" Failed on line {}. ".format(tb.tb_lineno) + str(e.message))
        sys.exit()

if __name__ == '__main__':
    main()
