# import relevant packages
import arcpy
import requests
import re
import time
import zipfile
import os
import sys


# define parameters
sz = sys.argv[1]
save_path = sys.argv[2]

############# get extent ##############
try: 
    # buffer to largest possible SZ buffer
    arcpy.analysis.Buffer(sz, "sz_with_lrg_donut_fc.shp", "9280 Meters", "FULL", "ROUND", "ALL")
    
    # check if spatial ref is WGS 84, if not convert (epsg = 4326)
    sr_bufsz = arcpy.Describe("sz_with_lrg_donut_fc.shp").SpatialReference.factoryCode
    if sr_bufsz != 4326:
        arcpy.management.Project("sz_with_lrg_donut_fc.shp", "sz_buf_reproj.shp", arcpy.SpatialReference(4326))
        sz = "sz_buf_reproj.shp"
    else:
        sz = "sz_with_lrg_donut_fc.shp"
    
    
    # get the extent of the buffered SZ
    sz_ext = arcpy.Describe(sz).extent
    sz_ext_xmin = sz_ext.XMin #lon, W
    sz_ext_xmax = sz_ext.XMax #lon, E
    sz_ext_ymin = sz_ext.YMin #lat, S
    sz_ext_ymax = sz_ext.YMax #lat, N

except:
    arcpy.AddError("Could not retrieve extent. Check input polygon.")
    sys.exit()
    
###########################

for rastype in ["EVH", "DTM"]:
    arcpy.AddMessage("Downloading LANDFIRE " + rastype + "...")
    
    if rastype == "EVH":
        ras_type = "200EVH"
    if rastype =="DTM":
        ras_type = "ELEV2020"
    
    try:
        # submit landfire request
        url = "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/submitJob?Layer_list=" + ras_type + "&Area_of_Interest=" + str(sz_ext_xmax) + "%20" +  str(sz_ext_ymin) + "%20" + str(sz_ext_xmin) + "%20" + str(sz_ext_ymax) 
        response = requests.get(url)
        open(save_path + "//landfire.txt", "wb").write(response.content)
    except:
        arcpy.AddError("Could not submit LANDFIRE request from URL: " + url)
        sys.exit()
    
    # get the job ID and wait a certain amount of time
    # then use below link with jobID to download the zip
    
    # open request HTML to find unique job ID
    with open(save_path + "//landfire.txt", "r") as file:
        for line in file.readlines():                                   # for every line in the job html
            match = re.search(r"(?:<\/b>)([\s\S]*?)(?=<br/>)", line)    # search for HTML that bounds the jobID
            #print(type(jobid))         
            if match is not None:                                       # most of the lines will return None     
                if "esri" in match.group():                             # lines with esri have other text we're not interested in
                    pass                                                # pass on them
                else:
                    jobid = match.group()[5:]                           # the line we want has 5 chars before the jobID that we aren't interested in
                    print(jobid)
    
    # check status of job
    job_url = "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/" + jobid
    status = 'esriJobSubmitted'
    while status != 'esriJobSucceeded':
        if status == 'esriJobFailed':
            # end the script if your API request fails
            arcpy.AddError("LANDFIRE download failed. Try: \n (1) Make sure your polygon is covered by LANDFIRE data (US and insular areas) \n (2) Try a smaller polygon \n (3) Check landfire.gov for scheduled maintenance.")
            sys.exit()
        arcpy.AddMessage("File processing...")
        time.sleep(10)
        # open the job status URL
        response = requests.get(job_url)
        open(save_path + "//landfire_processing.txt", "wb").write(response.content)
        # parse for the specific line
        with open(save_path + "//landfire_processing.txt", "r") as file:
            lines = file.readlines()
            job_status = lines[41]
            match = re.search(r"(?<=</b>)(.*?)(?=<br/>)", job_status) # find the job status
            status = match.group().strip()                            # set job status to eventually exit the loop
            arcpy.AddMessage(status)
    # when esriJobSubmitted go to zip URL
    # open the zip URL, write it to file:            
    zip_url = "https://lfps.usgs.gov/arcgis/rest/directories/arcgisjobs/landfireproductservice_gpserver/" + jobid + "/scratch/" + jobid + ".zip"    # URL seems to be the same for each zip request
    response = requests.get(zip_url)
    open(save_path + "//landfire_" + rastype + ".zip", "wb").write(response.content) # save zipped folder in predefined folder
    
    # now unzip the zipped file 
    with zipfile.ZipFile(save_path + "//landfire_" + rastype + ".zip", 'r') as zip_ref:
        zip_ref.extractall(save_path + "//landfire_" + rastype)
    
    # rename file 
    counter = 0 
    tf = True
    while tf == True:
        try:
            arcpy.management.Rename(save_path + "//landfire_" + rastype + "//" + jobid + ".tif", save_path + "//landfire_" + rastype + "//" + rastype + ".tif")
            tf = False # stope here because the save worked
        except: # otherwise try naming with the counter
            try:
                arcpy.management.Rename(save_path + "//landfire_" + rastype + "//" + jobid + ".tif", save_path + "//landfire_" + rastype + "//" + rastype + str(counter) + ".tif")
                tf = False # stop here if that worked
            except:
                counter = counter + 1
                # now tf is still true so it should go back through with counter increased by one and try again... 
                
    
        
# clean up files
try:
    os.remove(save_path + "//landfire_EVH.zip")
    os.remove(save_path + "//landfire_DTM.zip")
    os.remove(save_path + "//landfire.txt")
    os.remove(save_path + "//landfire_processing.txt")
    
except: 
        arcpy.AddWarning("Temporary files could not be deleted.")
