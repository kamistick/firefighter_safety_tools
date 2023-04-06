# firefighter_safety_tools

## Description

This repository holds an ArcGIS toolbox which contains useful tools for downloading and analyzing data related to wildland firefighter safety.  

## Software requirements 

The toolbox was built using ArcGIS Pro v. 3.0.0 and relies on Python v. 3.9.11. Therefore, it is recommended that the toolbox is used in comparable software versions. Some of the tools within the toolbox rely on ArcGIS geoprocessing tools within the Spatial Analyst tools. Therefore, an ArcGIS Pro license with Spatial Analyst tools is needed to use to the toolbox.

## User Guide 
To use the toolbox in the ArcGIS Pro GUI, download the .atbx file to an appropriate directory. Then add the toolbox to a new or existing project in ArcGIS Pro. To do this, navigate to and select FFS_tools.atbx and press 'OK'. The toolbox should appear in your catalog and can be expanded to display available tools. To use available tools, double click on their name and follow tool instructions. Tool descriptions are available by hovering over or clicking on the blue question mark at the top of the geoprocessing panel. Parameter descriptions and information are available by hovering over the “i” buttons to the left of parameter boxes. The .py scripts associated with each tool are embedded into the toolboxes but can be more easily referenced/downloaded directly from this repository. 

## Tool Documentation

The following tools are documented with a description, parameter specifications, and examples:

* [Download LANDFIRE EVH and DTM from Polygon](https://github.com/kamistick/firefighter_safety_tools#download-landfire-evh-and-dtm-from-polygon)

* [Safe Separation Distance (SSD)](https://github.com/kamistick/firefighter_safety_tools#safe-separation-distance-ssd)

* [Safe Separation Distance Evaluator (SSDE)](https://github.com/kamistick/firefighter_safety_tools#safe-separation-distance-evaluator-ssde)

### Download LANDFIRE EVH and DTM from Polygon 
#### Description
If you plan to use other tools in this toolbox, such as Safe Separation Distance (SSD) or Safe Separation Distance Evaluator (SSDE), or if you need to download vegetation height and elevation data for other purposes, this tool allows you to download LANDFIRE data. This tool uses LANDFIRE’s API (LandfireProductService) to download two raster datasets in TIF format: Existing Vegetation Height (EVH) and a digital terrain model (DTM). The LANDFIRE Layer IDs used to download the data are 200EVH, and ELEV2020, representing data from 2020 (see https://lfps.usgs.gov/helpdocs/productstable.html for more information). Raster data are downloaded according to the geographic area specified by the extent of the user’s input polygon. The resulting raster datasets will have an extent buffered by 9,280 meters, a distance appropriate for Safe Separation Distance Evaluator (SSDE) analysis. Output data will be saved in subfolders named “landfire_EVH” and “landfire_DTM”, respectively, created within the user specified output folder. Files are named according to their layer type (e.g. DTM.tif or EVH.tif). If running the tool multiple times with the same output folder, existing files will not be overwritten, instead file names will be appended with increasing values (e.g. if DTM.tif exists, DTM0.tif will be written next, then DTM1.tif etc.). Large input polygons may not successfully download due to the API’s file size constraints. It is suggested to use as small a study area as needed (e.g. a fire perimeter not a state boundary). Multi-state polygons will not successfully process. 
#### Parameters
| Name  | Explanation | Data Type
| ------------- | ------------- | ------------- |
| Polygon (study area or safety zone) |  An input polygon that defines your study area of interest. This polygon can be a potential safety zone, but if you are planning to examine multiple safety zones within a study area it is suggested to use a polygon that encompasses your entire study area for this step. This polygon must fall within the US, including insular areas.   |  Feature Layer, Feature Class, Shapefile  |
| Output folder | The folder within which your downloaded data will be saved. Subfolders will be generated automatically in this workspace. | Folder |

#### Example usage
The first parameter (‘Polygon (study area or safety zone)’) can either be selected from a folder by clicking on the folder icon and navigating to and selecting the polygon. If your polygon has already been added to your current map it can be selected from the dropdown menu. The ‘Output folder’ can be selected by clicking the folder icon and navigating to and selecting the target folder, or by typing in the path to the folder. 

### Safe Separation Distance (SSD)	
#### Description
This tool uses vegetation height, terrain slope, wind speed, and burning condition to map safe separation distance (SSD) across an entire landscape. More detailed information on the calculation of SSD can be found [here](https://doi.org/10.3390/fire5010005). SSD will be mapped according to the extent of the input raster datasets (Vegetation Height and Digital Terrain Model (DTM)). It is recommended to use the Download LANDFIRE EVH and DTM from Polygon tool prior to using this tool, so the input raster data are in the correct format. Vegetation height data from other sources will not produce accurate results, but elevation data from other sources may be acceptable. 
#### Parameters
| Name  | Explanation | Data Type
| ------------- | ------------- | ------------- |
| Vegetation Height  | LANDFIRE Existing Vegetation Height (EVH) raster. If downloaded using "Download LANDFIRE EVH and DEM from Polygon" tool this raster (in TIF format) can be found in your previously specified workspace, in a subfolder named "landfire_EVH”. | Raster Layer |
| Digital terrain model (DTM) | Digital terrain model raster. If downloaded using "Download LANDFIRE EVH and DTM from Polygon" tool this raster (in TIF format) can be found in your previously specified workspace, in a subfolder named "landfire_DTM". | Raster Layer |
| Wind Speed | The anticipated wind speed a user would like to investigate, selected from a dropdown menu: <br> Light (0-10 mph) <br> Moderate (11-20 mph) <br> High (>20 mph) | String |
| Burning Condition | The anticipated burning condition a user would like to investigate, selected from a dropdown menu: <br> Low <br> Moderate <br> Extreme | String |
| Workspace | The folder in which temporary files and subfolders will be created. | Folder |
| SSD  <br> *{output}* | The path (including name) of the output SSD raster. Once a workspace is specified, by default, this field is auto-populated with “SSD.tif” meaning a raster named “SSD.tif” will be saved in the previously specified Workspace folder. The location and name of the output can be changed. | Raster Layer |
#### Example usage
Vegetation Height and Digital Terrain Model (DTM) can be selected from the current map or navigated to and selected using the folder icon. If using ‘Download LANDFIRE EVH and DTM from Polygon’ the EVH raster will be in the folder named “landfire_EVH” and the DTM raster in “landfire_DTM” that were created when running the previous tool. Wind speed and burning condition can be selected from the dropdown menu. The SSD output must be named and placed in appropriate folders or geodatabase. Lastly, the workspace must be set to an appropriate folder in which temporary files will be generated.
### Safe Separation Distance Evaluator (SSDE)	
#### Description
This tool allows users to assess the suitability of a specific target safety zone based on vegetation height, terrain slope, wind speed, and burning condition. Detailed information on the development of SSDE can be found [here](https://doi.org/10.3390/fire5010005). This tool replicates the [Google Earth Engine version](https://firesafetygis.users.earthengine.app/view/ssde-en) of SSDE proposed in Campbell et. al. 2022. Users provide a polygon representing a potential safety zone, raster datasets containing LANDFIRE vegetation height and terrain values, a wind speed class, a burning condition class, output file names and locations, and a processing workspace.  It is recommended to use the Download LANDFIRE EVH and DTM from Polygon tool prior to using this tool, so the input raster data are in the correct format. Vegetation height data from other sources *will not* produce accurate results, but elevation data from other sources may be acceptable. 
#### Parameters
| Name  | Explanation | Data Type
| ------------- | ------------- | ------------- |
| Safety Zone | Polygon representing safety zone of interest. | Feature Layer, Feature Class |
| Vegetation Height | LANDFIRE Existing Vegetation Height (EVH) raster. If downloaded using "Download LANDFIRE EVH and DEM from Polygon" tool this raster (in TIF format) can be found in your previously specified workspace, in a subfolder named "landfire_EVH".  | Raster Layer |
| Digital terrain model (DTM) | Digital terrain model raster. If downloaded using "Download LANDFIRE EVH and DTM from Polygon" tool this raster (in TIF format) can be found in your previously specified workspace, in a subfolder named "landfire_DTM".  | Raster Layer |
| Wind Speed | The anticipated wind speed a user would like to investigate, selected from a dropdown menu: <br> Light (0-10 mph) <br> Moderate (11-20 mph) <br> High (>20 mph) | String |
| Burning Condition | The anticipated burning condition a user would like to investigate, selected from a dropdown menu: <br> Low <br> Moderate <br> Extreme | String |
| Workspace | The anticipated burning condition a user would like to investigate, selected from a dropdown menu: <br> Low  <br> Moderate <br> Extreme | Folder |
| pSSD *{output}* | The path (including name) of the output pSSD raster. <br> <br> Once a workspace is selected, by default, this field is auto-populated with “pSSD.tif” meaning a raster named “pSSD.tif” will be saved in the previously specified Workspace folder. The location and name of the output can be changed. <br> <br> The pSSD raster is continuous an indicates the proportional SSD, “which quantifies the extent to which a potential SZ polygon provides SSD from surrounding vegetation/flames, considering the average per-pixel SSD contained within a series of segments (or clusters of contiguous pixels) around the SZ polygon. Measured in percent, a pSSD of 100% or greater for a given pixel would mean that, factoring in vegetation height surrounding the polygon, slope, wind speed, and burn condition, the pixel’s location should provide sufficient SSD, should fire personnel opt to use this location as a SZ. Conversely, a pixel with a pSSD of less than 100% would indicate that firefighters located within that pixel may risk injury from burning vegetation outside the boundary of the polygon” (Campbell et. al 2022) A more detailed description of the computation of both SSD and pSSD can be found in the referenced paper. <br> <br> If saving in a folder, include TIF extension type (.tif) | Raster Layer |
| SSD Met *{output}* | The path (including name) of the output classified raster displaying whether or not SSD has been met. <br> Once a workspace is selected, by default, this field is auto-populated with “SSD_met.tif” meaning a raster named “SSD_met.tif” will be saved in the previously specified Workspace folder. The location and name of the output can be changed. <br> <br> A value of 0 indicates SSD has not been met. (pSSD < 100%) A value of 1 indicates that SSD has been met (pSSD ≥ 100%). Further description of SSD and <br> <br> If saving in a folder, include TIF extension type (.tif) | Raster Layer |
| Safest Point <br> *{output}* | Name (and directory or geodatabase) where the safest point feature will be written. If saving in a geodatabase, no file extension is required. If saving in a folder directory include .shp. <br> Once a workspace is selected, by default, this field is auto-populated with “safest_point.shp” meaning a shapefile named “safest_point.shp” will be saved in the previously specified Workspace folder. The location and name of the output can be changed.  <br><br>Example, shapefile: C:/users/avery_smith/SSDE/safest_point.shp <br> <br> Example, geodatabase: C:/users/avery_smith/project.gdb/safest_point | Feature Layer |

#### Example usage

The first parameter can either be selected from a folder by clicking on the folder icon and navigating to and selecting the polygon or, if your polygon as already been added to your current map, it can be selected from the dropdown menu. Vegetation Height and Digital Terrain Model (DTM) can be selected from the current map or navigated to and selected using the folder icon. If using ‘Download LANDFIRE EVH and DTM from Polygon’ the EVH raster will be in the folder named “landfire_EVH” and the DTM raster in “landfire_DTM” that were created when running the previous tool. Wind speed and burning condition can be selected from the dropdown menu. All three outputs, pSSD, SDD Met, and Safest Point, must be named and placed in appropriate folders or geodatabases. If saving in a geodatabase no extension (.tif, .shp, etc.) is needed. Lastly, the workspace must be set to an appropriate folder in which temporary files will be generated. 

## References
Campbell, M.J.; Dennison, P.E.; Thompson, M.P.; Butler, B.W. Assessing Potential Safety Zone Suitability Using a New Online Mapping Tool. Fire **2022**, 5, 5. https://doi.org/10.3390/fire5010005
