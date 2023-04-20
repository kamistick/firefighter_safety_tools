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

try:
    # check out sa extension
    arcpy.CheckOutExtension("spatial")
except:
    arcpy.AddError("Could not check out Spatial Analyst license. Are you licensed to use this extension?")
    sys.exit()

##############################
## create processing folder ##
##############################
processing_dir = sys.argv[7] + "//SSDE_processing" 
if not os.path.exists(processing_dir):
        os.mkdir(processing_dir)

arcpy.env.workspace = processing_dir
arcpy.env.scratchWorkspace = processing_dir
TempFolders = processing_dir


def run_ssde():
    ##############################
    ## get parameters from tool ##
    ##############################
    sz = sys.argv[2]
    vh = sys.argv[3]
    dtm = sys.argv[4]
    wc = sys.argv[5]
    bc = sys.argv[6]
    
    ###############################################
    ##   start by buffering SZ to get max extent ##
    ###############################################
    arcpy.analysis.Buffer(sz, "lrg_buffer.shp", "9280 Meters", "FULL", "ROUND", "ALL")  # won't use this later because it is in the wrong coord. sys. 
    arcpy.env.extent = arcpy.Describe("lrg_buffer.shp").extent                          # this way the UTM conversions will only be done within this processing extent
    
    ##############################
    ##   convert to UTM         ## 
    ##############################
    arcpy.AddMessage(ctime() + ": Converting coordinate systems...")
    # add centroid info to safety zone
    arcpy.management.AddGeometryAttributes(sz, "CENTROID")
    arcpy.management.CalculateGeometryAttributes(in_features = sz, geometry_property = [["CENTROID_X", "CENTROID_X"], ["CENTROID_Y", "CENTROID_Y"]], coordinate_format = "DD")
    with arcpy.da.SearchCursor(sz, ["CENTROID_X", "CENTROID_Y"]) as cursor:
        for row in cursor:
            centr_x = row[0] #longitude
            centr_y = row[1]
    utm_num = (math.floor((centr_x + 180)/6 )%60) + 1
    epsg_code = utm_num + 26900
    utm_sr = arcpy.SpatialReference(epsg_code)
    
    # make sure the rasters aren't already in UTM
    # if they are not, convert them, and rename variable to reprojected raster.
    sr1 = arcpy.Describe(vh).spatialReference
    sr2 = arcpy.Describe(dtm).spatialReference
    sr3 = arcpy.Describe(sz).spatialReference
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
    if sr3.name != utm_sr.name:
        arcpy.management.Project(sz, "sz_reproj.shp", utm_sr)
        sz = "sz_reproj.shp"
        arcpy.AddMessage("Safety zone polygon converted to UTM coordinates.")
    else:
        arcpy.AddMessage("Safety zone polygon in UTM coordinates.")
    arcpy.AddMessage(ctime() + ": Done.")
    # clear the extent to allow geoprocessing to determine appropriate extents
    arcpy.env.extent = None
    
    ##############################
    ##       check overlap      ##
    ##############################
    arcpy.AddMessage(ctime() + ": Checking overlap...")
    # make sure the polygon overlaps both rasters entirely, else throw an error
    cursor = arcpy.da.SearchCursor(sz, ['SHAPE@'])
    for row in cursor:
        geom_sz = row[0]
        sz_extent = row[0].extent
    vh_extent = arcpy.Describe(vh).extent
    dtm_extent = arcpy.Describe(dtm).extent
    del cursor
    if vh_extent.contains(sz_extent):
        arcpy.AddMessage("Vegetation height raster contains proposed safety zone.")
    else:
        arcpy.AddError("Vegetation height raster does not contain extent of safety zone.")
        sys.exit() 
    
    if dtm_extent.contains(sz_extent):
        arcpy.AddMessage("DTM raster contains proposed safety zone.")
    else:
        arcpy.AddError("DTM raster does not contain extent of safety zone.")
        sys.exit() 
        
    arcpy.AddMessage(ctime() + ": Done.")
    
    ###############################
    ##   crop to safety zone+    ##
    ##     also make buffers     ##
    ###############################
    arcpy.AddMessage(ctime() + ": Getting slope and safety zone buffers...")
    # use Extract by Mask to get slope, veg height just in the polygon
    # first get a slope raster from the DTM
    # get units
    dtm_linearunit = (arcpy.Describe(dtm).spatialReference.linearUnitName.upper())
    # get slope raster 
    slope = Slope(dtm, output_measurement = "PERCENT_RISE", z_unit = dtm_linearunit)
    # get large buffer with max possible SSD (including SZ)
    arcpy.analysis.Buffer(sz, "sz_with_lrg_donut_fc.shp", "9280 Meters", "FULL", "ROUND", "ALL")
    # this EXCLUDES the safety zone
    arcpy.analysis.Buffer(sz, "lrg_donut_fc.shp", "9280 Meters", "OUTSIDE_ONLY", "ROUND", "ALL")
    # then EBM slope and veg height to DONUT + SZ (later use EBM to just look at either)
    vh_ebm = ExtractByMask(vh, "sz_with_lrg_donut_fc.shp")
    slope_ebm = ExtractByMask(slope, "sz_with_lrg_donut_fc.shp")
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
    in_conditional_raster = slope_ebm # this is the slope raster, whether or not its the EBM version
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
    vh_reclass = Reclassify(in_raster = vh_ebm,  reclass_field = "Value", remap = RemapValue(vals))
    vh_meters = Raster(vh_reclass)/100.0
    
    # if you get an error on Reclassify (999999) close Arc and close the python shell if its open. 
    arcpy.AddMessage(ctime() + ": Done.")
    
    #########################
    ##   Calculate SSD     ##
    #########################
    arcpy.AddMessage(ctime() + ": Calculating SSD...")
    ## for the entire input safety zone
    ssd = 8 * vh_meters * slope_remap
        
    ## now we just want to look at the donut
    # EBM SSD to the donut
    ssd_lrg_donut = ExtractByMask(ssd, "lrg_donut_fc.shp")
    # find the maximum SSD
    max_ssd_lrg_donut = arcpy.management.GetRasterProperties(ssd_lrg_donut, "MAXIMUM")
    # make a new smaller donut using the max value
    max_string = str(max_ssd_lrg_donut) + " Meters"
    arcpy.analysis.Buffer(sz, "sml_donut_buf_fc.shp", max_string, "OUTSIDE_ONLY", "ROUND", "ALL")
    # EBM to smaller donut
    ssd_sml_donut = ExtractByMask(ssd, "sml_donut_buf_fc.shp")
    
    arcpy.AddMessage(ctime() + ": Done.")
    ##############################
    ##   image segmentation     ##
    ##############################
    arcpy.AddMessage(ctime() + ": Segmenting SSD raster...")
    # take smaller donut and use segment mean shift
    seg_raster = SegmentMeanShift(in_raster = ssd_sml_donut, spectral_detail = 8,
                                  spatial_detail = 8, min_segment_size = 20,
                                  max_segment_size = -1)
    seg_raster.save(sys.argv[7] + "seg_ras.tif")
    arcpy.AddMessage(ctime() + ": Done.")
    ##############################
    ##   pSSD calculations      ## 
    ##############################
    arcpy.AddMessage(ctime() + ": Calculating pSSD...")
    
    ## start by getting the euclidian distance for each segment
    # get a list of OIDs for each segment/group of segments
    cursor = arcpy.da.SearchCursor(sys.argv[7] + "seg_ras.tif", ['Value'])
    segment_ids = []
    for row in cursor:
        segment_ids.append(row[0])
    raslist = []
    for segment_id in segment_ids:
        segment = SetNull(seg_raster, 1, "VALUE <> " + str(segment_id))
        # euclidian distance
        dist1 = DistanceAccumulation(segment)
        dist = ExtractByMask(dist1, sz)
        ssd_ebm = ExtractByMask(ssd_sml_donut, segment)
        mean_ssd = arcpy.management.GetRasterProperties(ssd_ebm, "MEAN").getOutput(0)
        # divide euclid. dist. by mean and save
        pssd = dist/float(mean_ssd)
        # list of all pSSD rasters for next step
        raslist.append(pssd)
        
    
    ## use list of pssd rasters to get raster with minimum across all pssds
    minimum_pssd = CellStatistics(raslist, "MINIMUM")
    minimum_pssd.save(sys.argv[8])
    
    arcpy.AddMessage(ctime() + ": Done.")
    
    ##################################################
    ##   get safest point and SSD met/not  met      ##
    ##################################################
    arcpy.AddMessage(ctime() + ": Determining areas where SSD has been met...")
    # use Con to determine areas >1.0 (safe, SSD met) and <1.0 (unsafe, SSD not met)
    binary_pssd = Con(minimum_pssd, 1, 0, "Value > 1.0")
    binary_pssd.save(sys.argv[9])
    arcpy.AddMessage(ctime() + ": Done.")
    arcpy.AddMessage(ctime() + ": Getting safest point...")
    # get maximum value of minimum_pssd
    max_minimum_pssd =  arcpy.management.GetRasterProperties(minimum_pssd, "MAXIMUM").getOutput(0)
    # set everything that is not the max value to NoData
    max_pixel_only = SetNull(minimum_pssd, max_minimum_pssd, "VALUE <> " + str(max_minimum_pssd))
    # convert the new raster to a point (should result in one point)
    arcpy.conversion.RasterToPoint(max_pixel_only, sys.argv[10])
    arcpy.AddMessage(ctime() + ": Done.")
    
    # check in sa extension
    arcpy.CheckInExtension("spatial")

# run SSD function
run_ssde()

    

# clean up files 
def delete_files():
    arcpy.Delete_management(processing_dir)
    seg_ras = Raster(sys.argv[7] + "seg_ras.tif")
    arcpy.Delete_management(seg_ras)

try:
    delete_files()
except:
    arcpy.AddError("Could not delete temporary files.")
    sys.exit()
