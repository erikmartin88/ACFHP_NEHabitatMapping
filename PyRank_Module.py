#-------------------------------------------------------------------------------
# Name:        Python ranking module.
# Purpose:      Rank values in a list using the "DENSE" method
#
# Author:      Erik Martin. Utilizes Heungsub Lee's ranking.py script
#               http://pythonhosted.org/ranking/#ranking.Ranking
#
# Created:     31/07/2013
# Copyright:   (c) emartin 2013 emartin@tnc.org
#-------------------------------------------------------------------------------
import sys, myGlobals as mg, arcpy

from time import strftime
from ranking import (Ranking, DENSE)

def myRank(fc, valField, rankField, order):
    try:
        #get list of values from value field
##        arcpy.AddMessage("Getting values from input field at " + strftime("%H:%M:%S"))
        valueList = []
        with arcpy.da.SearchCursor(fc, valField) as rows:
            for row in rows:
                valueList.append(row[0])
        #rank the values in the list and write rank & value to a dict
        if order == "D":
            scores = sorted(valueList, reverse = True)
            rankDict = {}
            for rank, score in Ranking(scores, DENSE):
                    rankDict.update({score:rank+1})
        elif order == "A":
            scores = sorted(valueList)
            rankDict = {}
            for rank, score in Ranking(scores, DENSE, reverse="True"):
                    rankDict.update({score:rank+1})
        else:
            print("Enter either 'A' or 'D' for the sort order")
            arcpy.AddMessage("Enter either 'A' or 'D' for the sort order")
            sys.exit()



        #write the ranks back to the rankField
        fields = (valField, rankField)
        with arcpy.da.UpdateCursor(fc, fields) as updateRows:
            for updateRow in updateRows:
                joinFieldValue = updateRow[0]
                if (joinFieldValue in rankDict) and (joinFieldValue != None):
                    updateRow[1] = rankDict[joinFieldValue]
                updateRows.updateRow(updateRow)

        del rankDict

    except Exception, e:
        tb = sys.exc_info()[2]
        print ("Problem with the PyRank module...")
        print "Line {}".format(tb.tb_lineno)
        print e.message
        sys.exit()

def main():
    print("starting script at " + strftime("%H:%M:%S"))
    myRank(r"C:\Users\emartin\Desktop\test.gdb\wetlands", "_FETCH", "testRank", "A")

if __name__ == '__main__':
    main()
