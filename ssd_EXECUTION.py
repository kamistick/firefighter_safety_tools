## The University of Utah and the operator of this website (along with their employees or agents) are not responsible
## for any decisions or results of the decisions that you make. You assume all risk arising from reliance on this 
## website and, by using this website you agree to hold the University of Utah and the operation of the website harmless
## for damages arising out of your actions, whether or not in reliance on information provided through the website.

## The information provided through the website application is given “as is”. To the maximum extent permitted by applicable
## law, the University of Utah and the operator of the website disclaim all representations and warranties, expressed or 
## implied, with respect to such information, services, products, and materials, including without limitation any implied
## warranties or merchantability, fitness for a particular purpose and noninfringement. In no event will the University of
## Utah or website operator be liable for any consequential, indirect, incidental, special, or punitive damages, however
## caused and under any theory of liability (including negligence), arising from your use of the website or the provision
## of the information, services, products, and materials provided to or by the University of Utah or the website operator,
## even if the University of Utah or website operator has been advised of the possibility of such damages.


## import relevant packages

import arcpy
import sys
from arcpy import env
from arcpy.sa import *
from time import ctime
from time import time
import os
import math
import shutil

arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "50%"

# check out sa extension
try:
    arcpy.CheckOutExtension("spatial")
except:
    arcpy.AddError("Could not check out Spatial Analyst license. Are you licensed to use this extension?")
    sys.exit()

##############################
## create processing folder ##
##############################
try: 
    processing_dir = sys.argv[6] + "//processing"
    if not os.path.exists(processing_dir):
            os.mkdir(processing_dir)
    
    arcpy.env.workspace = processing_dir
    arcpy.env.scratchWorkspace = processing_dir
    TempFolders = processing_dir
except: 
    arcpy.AddError("Could not create temporary processing folder.")
    sys.exit()


def run_ssd():
    ##############################
    ## get parameters from tool ##
    ##############################
    
    tc = sys.argv[1]      # boolean: do you want to use a buffer? (checkbox, FAKE boolean, actually a string 'false' or 'true')
    if tc =='true':                # if yes, last one is the size of buffer, a string IN METERS (string)
        vh = sys.argv[2]
        dtm = sys.argv[3]
        wc = sys.argv[4]
        bc = sys.argv[5]
    
    ###############################################
    ##   set processing for sr conversion        ##
    ###############################################
    arcpy.env.extent = arcpy.Describe(vh).extent
    
    ##############################
    ##   convert to UTM         ## 
    ##############################
    arcpy.AddMessage(ctime() + ": Getting coordinate system information...")
    sr_input = arcpy.Describe(vh).spatialReference
    sr_latlon = arcpy.SpatialReference(4326)
    ext = arcpy.Describe(vh).extent
    xmin = ext.XMin
    xmax = ext.XMax
    ymin = ext.YMin
    ymax = ext.YMin
    centr_x = (xmax + xmin)/2
    centr_y = (ymin+ymax)/2
    pt = arcpy.Point(centr_x, centr_y)
    ptg = arcpy.PointGeometry(pt, sr_input).projectAs(sr_latlon)
    centr_x_latlon = ptg.firstPoint.X
    centr_y_latlon = ptg.firstPoint.Y
    utm_num = (math.floor((centr_x_latlon + 180)/6 )%60) + 1
    epsg_code = utm_num + 26900
    utm_sr = arcpy.SpatialReference(epsg_code)
    
    # make sure the rasters aren't already in UTM
    # if they are not, convert them, and rename variable to reprojected raster.
    sr1 = arcpy.Describe(vh).spatialReference
    sr2 = arcpy.Describe(dtm).spatialReference
    if sr1.name != utm_sr.name:
        arcpy.management.ProjectRaster(vh, 'vh_reproj.tif', utm_sr, "NEAREST") # these need to be written to file, can't just be held in memory.
        vh = 'vh_reproj.tif'
        arcpy.AddMessage("Vegetation height raster converted to UTM coordinates.")
    else:
        arcpy.AddMessage("Vegetation height raster in UTM coordinates.")
    if sr2.name != utm_sr.name:
        arcpy.management.ProjectRaster(dtm, 'dtm_reproj.tif', utm_sr, "BILINEAR")
        dtm = 'dtm_reproj.tif'
        arcpy.AddMessage("DTM raster converted to UTM coordinates.")
    else:
        arcpy.AddMessage("DTM raster in UTM coordinates.")
    
    arcpy.AddMessage(ctime() + ": Done.")
    
    # clear the extent to allow geoprocessing to determine appropriate extents
    arcpy.env.extent = None
    
    ###############################
    ##   get slope               ##
    ###############################
    # use Extract by Mask to get slope, veg height just in the polygon
    # first get a slope raster from the DTM
    # get units
    dtm_linearunit = (arcpy.Describe(dtm).spatialReference.linearUnitName.upper())
    # get slope raster 
    slope = Slope(dtm, output_measurement = "PERCENT_RISE", z_unit = dtm_linearunit)
    
    arcpy.AddMessage(ctime() + ": Done.")
    
    ##############################################
    ##   turn slope into multiplicative term    ##
    ##############################################
    arcpy.AddMessage(ctime() + ": Getting multiplicative term for SSD...")
    # raster calculations: 
    # SSD = 8 * VH * (delta)
    # where (delta) relies on wind speed, slope, burning condition
    # slope is PER pixel, other two are constant across landscape
    
    ## make a list of multiplactive factor (mf) values to pull from
    if wc == "Light (0-10 mph)" and bc == "Low":
        mfl = [0.8, 1, 1, 2]
    if wc == "Light (0-10 mph)" and bc == "Moderate":
        mfl = [1,1,1.5,2]
    if wc == "Light (0-10 mph)" and bc == "Extreme":
        mfl = [1,1.5,1.5,3]
    if wc == "Moderate (11-20 mph)" and bc == "Low":
        mfl = [1.5,2,3,4]
    if wc == "Moderate (11-20 mph)" and bc == "Moderate":
        mfl = [2,2,4,6]
    if wc == "Moderate (11-20 mph)" and bc == "Extreme":
        mfl = [2,2.5,5,6]
    if wc == "High (>20 mph)" and bc == "Low":
        mfl = [2.5,3,4,6]
    if wc == "High (>20 mph)" and bc == "Moderate":
        mfl = [3,3,5,7]
    if wc == "High (>20 mph)" and bc == "Extreme":
        mfl = [3,4,5,10]
    arcpy.AddMessage(ctime() + ": Done.")
    ## use Con to reclassify slope into the delta value for SSD calculation
    arcpy.AddMessage(ctime() + ": Calculating slope/wind factor...")
    in_conditional_raster = slope # this is the slope raster, whether or not its the EBM version
    where_clause0 = "Value >= 0 And Value < 7.5"       #mlf[0]
    where_clause1 = "Value >= 7.5 And Value < 22.5"    #mlf[1]
    where_clause2 = "Value >= 22.5 And Value < 41"     #mlf[2]
    where_clause3 = "Value >= 41"                       #mlf[3]
    slope_remap = Con(in_conditional_raster, mfl[0],
        Con(in_conditional_raster, mfl[1],
            Con(in_conditional_raster, mfl[2],
                Con(in_conditional_raster, mfl[3], where_clause = where_clause3), where_clause2), where_clause1), where_clause0)
    
    arcpy.AddMessage(ctime() + ": Done.")
    
    #######################################################################
    ##   Change landfire EVH classified values into continous meters     ##
    #######################################################################
    arcpy.AddMessage(ctime() + ": Reclassify LANDFIRE EVH to meters...")
    # GENERATE REMAP VALUE LIST
    # calculations done on NUMERIC, all final values must be INTEGERS
    # initiate empty list first
    vals = []
    # values 11 thru 100 ==> 0
    for x in range(11,101):
        vals.append([x,0])
    # 101 thru 199 ==> value - 100 meters
    for x in range(101, 200):
        vals.append([x, (x-100)*100])
    # 201 (NO 200) - 230 ==> value - 200 / 10
    for x in range(201, 231):
        vals.append([x, int(((x-200)/10.0)*100)])
    # 301-310 ==> value - 300 / 10
    for x in range(301,311):
        vals.append([x,int(((x-300)/10.0)*100)])
    
    ## next need to reclassify EVH to actually be meters
    vh_reclass = Reclassify(in_raster = vh,  reclass_field = "Value", remap = RemapValue(vals))
    vh_meters = Raster(vh_reclass)/100.0
    
    # if you get an error on Reclassify (999999) close Arc and close the python shell if its open. 
    arcpy.AddMessage(ctime() + ": Done.")
    
    #########################
    ##   Calculate SSD     ##
    #########################
    arcpy.AddMessage(ctime() + ": Calculating SSD...")
    ## for the entire input safety zone
    ssd = 8 * vh_meters * slope_remap
    
    ssd.save(sys.argv[7])
    arcpy.AddMessage(ctime() + ": Done.")
    # check in sa extension
    arcpy.CheckInExtension("spatial")

# run SSD function
run_ssd()

# clean up files 
def delete_files():
    arcpy.Delete_management(processing_dir)
try:
    delete_files()
except:
    arcpy.AddError("Could not delete temporary files.")
    sys.exit()
