
<html>
<head>
</head>
<body>

# Table of Contents
[Team Members](#team-members)

[Dependencies](#dependencies)

[Project Summary](#project-summary)

[Processing Steps](#processing-steps)

# <a name="team-members"></a>Team Members

* "Ian Erickson" <ierickson@tableau.com>
* "Arielle Simmons-Steffen" <asimmons-steffen@tableau.com>
* "Matt Kenny" <mkenny@tableau.com>

# <a name="dependencies"></a>Dependencies

ShieldLabels.py:

fiona
shapely
re
os
sys
stat
shutil

Nodify.py:

fiona
time
shapely

# <a name="project-summary"></a>Project Summary

The scripts ShieldLabels.py and Nodify.py are designed to generate shield label points from the shapefile extract of osm derived datasets.


<a name-"processing-steps"></a>Processing Steps

1) User projects (EPSG: 3857) and spatially selects the region (either USA or Global) that will be run through ShieldLabels.py and Nodify.py.  A 'ref' tag is REQUIRED to be in this dataset.

**User must take caution to make sure the utf-8 encoding is preserved during the spatial select.**

2) The spatially selected boundaries are run through ShieldLabels.py. This script parses the 'ref' tag into the necessary 
	['label'] field and a ['shield_typ'] field types. IF THE 'ref' tag is not called 'ref' tag. Line 84 in the function 
	ShieldLabels.ShieldLabels.dissolve is where you can reset the field name. In order to run ShieldLabels.py the user must input the following: 
	
	inputFile = spatially selected USA/Global osm_motorways shapefile
	
	outputFile = a shapefile named of the users choosing
	
	region = a tag declaring whether to parse the spatially selected shapefile by it's region. Can be either 'USA' or 
	'Global'
	
	Example of input parameters:
	
	inputFile = r"I:\It_26\Python_Label_Shields_tool\code_for_data\osm_motorways_usa.shp"
    outputFile = r"I:\It_26\Python_Label_Shields_tool\data_result\osm_motorways_usa_shield_lines.shp"
    region = USA

3) Use shptree to generate a qix file for the new shield lines dataset
	
4) The outputFile from ShieldLabels.py is then run through Nodify.py. The output of Nodify.py will create the final dataset
   needed for inputing road shield points into the service. First step is to generate nodes (see LineTools.add_nodes) at a
   set interval=2000.
   
   Make sure that you use QGIS on the output shapefile to set ['PROCESSED'] = 'N' (see line: 144), before using it as an input for another file!
   is expected that you will run Nodify.LineTools.thin_node FIVE times for each region and create FIVE output files, beginning with
   radius: 4000.
   
   Example of input parameters:
   
    input_file = r"D:\work\osm_motorways\osm_world_labels.shp"
    output_file = r"D:\work\osm_motorways\osm_world_label_nodes_2000.shp"
    complete_file = r"D:\work\osm_motorways\osm_world_label_points_6000.shp"

    LineTools.add_nodes(input_file=input_file, output_file=output_file, interval=2000)
    LineTools.thin_nodes(input_file=output_file, output_file=complete_file, group_field='label', radius=6000)
   
   Example inputs for 'radius' are:
   
   USA:
   * note: generate a new qix file for each of the output files before using it as an input
   
		- radius: 50000 (note: run on the 30000 output file)
		  zoom: 9
		  
		- radius: 30000 (note: run on the 16000 output file)
		  zoom: 10
		  
		- radius: 16000 (note: run on the 8000 output file)
		  zoom: 11
		  
		- radius: 8000 (note: run on the 4000 output file)
          zoom: 12
		
		- radius: 4000
		  zoom: 13
   
    Global:
    * note: generate a new qix file for each of the output files before using it as an input
   
		- radius: 50000 (note: run on the 30000 output file)
		  zoom: 9
		  
		- radius: 30000 (note: run on the 16000 output file)
		  zoom: 10
		  
		- radius: 16000 (note: run on the 8000 output file)
		  zoom: 11
		  
		- radius: 8000 (note: run on the 4000 output file)
          zoom: 12
		
		- radius: 4000
		  zoom: 13
    
5) The user takes the 5 output files from Nodify.py and sets the zoom attribute according to the radius parameter (see above).
   Merge all 5 output files together into ONE shapefile. Generate a qix file. MANUALLY REMOVE ANY INCORRECT POINTS THAT WERE CAUSED BY 
   THE SPATIAL SELECT. 


For more details please see in-line comments in ShieldLabels.py & Nodify.py.

</body>
</html>