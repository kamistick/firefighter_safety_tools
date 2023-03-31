# firefighter_safety_tools

## Description

This repository holds an ArcGIS toolbox which contains useful tools for downloading and analyzing data related to wildland firefighter safety. The user guide 

## Software requirements 

The toolbox was built using ArcGIS Pro v. 3.0.0 and relies on Python v. 3.9.11. Therefore, it is recommended that the tool is used in a comparable software versions. Some of the tools within the toolbox rely on ArcGIS geoprocessing tools within the Spatial Analyst tools. Therefore, an ArcGIS Pro license with Spatial Analyst tools is needed to use to the toolbox.

## User Guide 
To use the toolbax in the ArcGIS Pro GUI, download the .atbx file to an appropriate directory. Then add the toolbox to a new or existing project in ArcGIS Pro. To do this, navigate to and select FFS_tools.atbx and press 'OK'. The toolbox should appear in your catalog and can be expanded to display available tools. The .py scripts associated with each tool are embedded into the toolboxes but can be more easily referenced/downloaded directly from this repository. 
## Tool Documentation

The following tools are documented with a description, parameter specifications, and examples:

* [Download LANDFIRE EVH and DTM from Polygon](https://github.com/kamistick/firefighter_safety_tools#download-landfire-evh-and-dtm-from-polygon)

* [Safe Separation Distance (SSD)](https://github.com/kamistick/firefighter_safety_tools#safe-separation-distance-ssd)

* [Safe Separation Distance Evaluator (SSDE)](https://github.com/kamistick/firefighter_safety_tools#safe-separation-distance-evaluator-ssde)

### Download LANDFIRE EVH and DTM from Polygon 
#### Description
If you plan to use other tools in this toolbox, such as Safe Separation Distance (SSD) or Safe Separation Distance Evaluator (SSDE), or if you need to download vegetation height and elevation data for other purposes, this tool allows you to download LANDFIRE data. This tool uses LANDFIRE’s API (LandfireProductService) to download two raster datasets in TIF format: Existing Vegetation Height (EVH) and a digital terrain model (DTM). The LANDFIRE Layer IDs used to download the data are 200EVH, and ELEV2020, representing data from 2020 (see https://lfps.usgs.gov/helpdocs/productstable.html for more information). Raster data are downloaded according to the geographic area specified by the extent of the user’s input polygon. The resulting raster datasets will have an extent buffered by 9280 meters, a distance appropriate for Safe Separation Distance Evaluator (SSDE) analysis. Output data will be saved in subfolders named “landfire_EVH” and “landfire_DTM”, respectively, created within the user specified output folder. Files are named according to their layer type (e.g. DTM.tif or EVH.tif). If running the tool multiple times with the same output folder, existing files will not be overwritten, instead file names will be appended with increasing values (e.g. if DTM.tif exists, DTM0.tif will be written next, then DTM1.tif etc.). Large input polygons may not successfully download due to the API’s file size constraints. It is suggested to use as small a study area as needed (e.g. a fire perimeter not a state boundary). Multi-state polygons will not successfully process. 
#### Parameters
Table
#### Example usage
The first parameter (‘Polygon (study area or safety zone)’) can either be selected from a folder by clicking on the folder icon and navigating to and selecting the polygon. If your polygon has already been added to your current map it can be selected from the dropdown menu. Figure 2 shows a screenshot of example parameters where ‘sz.shp’ is a polygon shapefile representing a safety zone that has not been added to the current map. The ‘Output folder’ can be selected by clicking the folder icon and navigating to and selecting the target folder. In Figure 2 a folder named ‘AZ’ has been selected. 

### Safe Separation Distance (SSD)	
#### Description
#### Parameters
#### Example usage

### Safe Separation Distance Evaluator (SSDE)	
#### Description
#### Parameters
#### Example usage

A little bit about this. 
