######################################################################
## Erik Martin, The Nature Conservancy, emartin@tnc.org, May 2013
##
## Script to tier dams into 5% bins based on FinalRank
##
## Modified2/21/13 - converted to arcpy.da cursors, added try/except
######################################################################
import arcpy, myGlobals as mg
arcpy.env.overwriteOutput = True
logger = mg.rootLogger


def tier(fc, valField, tierField):
    logger.info("...tiering up...")
    try:
        #Find the max value in the value field to use in % calcs
        list = []                                   	#initialize the list
        fields = (valField)
        with arcpy.da.SearchCursor(fc, fields) as rows: #open the search cursor
            for row in rows:                            #start the loop
                val = row[0]            				#get the values from the ValueField
                list.append(val)                        #append each value to the list
        maxVal = float(max(list))                          #find the max value in the list


        fields = (valField, tierField)
        with arcpy.da.UpdateCursor(fc, fields) as rows: #open the update cursor
            for row in rows:                            #start the loop
                val = row[0]            				#get the values from the Value Field
                if ((float(val) / maxVal * 100) <= 5):
                    row[1] =1
                elif ((float(val)) / maxVal * 100 >5) and ((float(val)) / maxVal * 100 <=10):
                    row[1] =2
                elif ((float(val)) / maxVal * 100 >10) and ((float(val)) / maxVal * 100 <=15):
                    row[1] =3
                elif ((float(val)) / maxVal * 100 >15) and ((float(val)) / maxVal * 100 <=20):
                    row[1] =4
                elif ((float(val)) / maxVal * 100 >20) and ((float(val)) / maxVal * 100 <=25):
                    row[1] =5
                elif ((float(val)) / maxVal * 100 >25) and ((float(val)) / maxVal * 100 <=30):
                    row[1] =6
                elif ((float(val)) / maxVal * 100 >30) and ((float(val)) / maxVal * 100 <=35):
                    row[1] =7
                elif ((float(val)) / maxVal * 100 >35) and ((float(val)) / maxVal * 100 <=40):
                    row[1] =8
                elif ((float(val)) / maxVal * 100 >40) and ((float(val)) / maxVal * 100 <=45):
                    row[1] =9
                elif ((float(val)) / maxVal * 100 >45) and ((float(val)) / maxVal * 100 <=50):
                    row[1] =10
                elif ((float(val)) / maxVal * 100 >50) and ((float(val)) / maxVal * 100 <=55):
                    row[1] =11
                elif ((float(val)) / maxVal * 100 >55) and ((float(val)) / maxVal * 100 <=60):
                    row[1] =12
                elif ((float(val)) / maxVal * 100 >60) and ((float(val)) / maxVal * 100 <=65):
                    row[1] =13
                elif ((float(val)) / maxVal * 100 >65) and ((float(val)) / maxVal * 100 <=70):
                    row[1] =14
                elif ((float(val)) / maxVal * 100 >70) and ((float(val)) / maxVal * 100 <=75):
                    row[1] =15
                elif ((float(val)) / maxVal * 100 >75) and ((float(val)) / maxVal * 100 <=80):
                    row[1] =16
                elif ((float(val)) / maxVal * 100 >80) and ((float(val)) / maxVal * 100 <=85):
                    row[1] =17
                elif ((float(val)) / maxVal * 100 >85) and ((float(val)) / maxVal * 100 <=90):
                    row[1] =18
                elif ((float(val)) / maxVal * 100 >90) and ((float(val)) / maxVal * 100 <=95):
                    row[1] =19
                elif ((float(val)) / maxVal * 100 >95) and ((float(val)) / maxVal * 100 <=100):
                    row[1] =20
                else:
                    logger.error("There was a problem calculating Tiers...")
                rows.updateRow(row)

    except Exception as e:
        logger.error("The was a problem with the Tier Module... " + e.message)
