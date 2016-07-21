# -*- coding: utf-8 -*-
__author__ = 'asimmons'

"""The purpose of this script is to create road shield lines based on clipped data imports from osm.
Outputs are this script are intended to be used as the input data into the "Nodify.py" script for
creating road shield points for the USA and GLOBAL dataset.

The input data is expected to be a Multi/LineString shapefile that:
 1) contains a an attribute called ['ref']
 2) is pre-clipped to a particular region (either "USA" or "GLOBAL")

The pre-process functions (def dissolve, and def split_and_duplicate_segments) create two TEMPORARY files which
are the dissolved and duplicated segments extracted from the original input
file. These files are created within the folder the script runs from -- and can be deleted after
all processing steps are complete.

The rest of the functions in the script are designed for creating the attributes that are needed in
order to run Nodify.py. These include a ['label'] field and a ['shield_typ'] field. Other fields are
included such as ['seg_len'] and ['label_len'] because they are required inputs for labeling
display rules.

Below is an example of the required inputs for this script:

    inputFile = r"I:\It_26\Python_Label_Shields_tool\code_for_data\osm_motorways_usa.shp"
    outputFile = r"I:\It_26\Python_Label_Shields_tool\data_result\osm_motorways_usa_shield_lines.shp"
    region = USA

"""

import fiona
from shapely.geometry import shape, mapping,Polygon
from shapely.ops import cascaded_union
import re
import os
import sys
import stat
import shutil



class ShieldLabels:

    def process_file(self, inFile, outFile, region):
        # process file is the final processing step which writes to the user-defined outputFile
        with fiona.open(inFile, 'r', encoding='utf-8') as input:
            input_driver = input.driver
            input_crs = input.crs
            input_schema = input.schema.copy()
            input_schema['properties']['shield_typ'.encode("utf-8")] = 'str:254'
            input_schema['properties']['label'.encode("utf-8")] = 'str:254'
            input_schema['properties']['seg_len'] = 'int:10'
            input_schema['properties']['label_len'] = 'int:10'
            with fiona.open(outFile, 'w', driver=input_driver, crs=input_crs, schema=input_schema, encoding='utf-8') as output:
                for item in input:
                    shield_val = self.create_shield_type(item,region)
                    item['properties']['shield_typ'] = shield_val
                    label_val = self.create_label(item,region)
                    item['properties']['label'] = label_val
                    segment_length_val = shape(item['geometry']).length
                    item['properties']['seg_len'] = segment_length_val
                    # remove items that have no value in the label field
                    if label_val is None:
                        continue
                    # measure the length of characters in the label field
                    label_length_val = len(label_val)
                    # for USA region only, remove items that have a label length >5 or = 0
                    if region == "USA" and (label_length_val > 5 or label_length_val == 0):
                        continue
                    item['properties']['label_len'] = label_length_val

                    output.write({'properties': item['properties'],'geometry': mapping(shape(item['geometry']))})

    def dissolve (self, inFile, outFile):
        # create dictionary for storing the uniqueRefs
        uniqueRefs = {}
        with fiona.open(inFile, 'r', encoding='utf-8') as input:
            input_driver = input.driver
            input_crs = input.crs
            input_schema = {'geometry': 'MultiLineString','properties': {'ref'.encode("utf-8"): 'str:254'}}
            with fiona.open(outFile, 'w', driver=input_driver, crs=input_crs, schema=input_schema, encoding='utf-8') as output:
                for item in input:
                    # extract the key, if the 'ref' attribute is NOT called 'ref' 
                    # you can insert the different attribute name HERE (and only HERE).
                    key = item['properties']['ids_and_re']
                    geom = shape(item['geometry'])
                    # find all motorways within the New Zealand mainland
                    # and remove all letters per  BUGZID: 106030
                    newZeaBox = [(17920614.01, -4033681.682),(20362002, -4054837.565),(20357771.35, -6073108.484),(17683668.157,-6068877.308)]
                    newZeaPoly = Polygon(newZeaBox)
                    if geom.within(newZeaPoly):
                        key = re.sub(r'\D',"", key)
                    if not geom.type.startswith('Multi'):
                        geom = [geom]
                    for g in geom:
                        if key in uniqueRefs:
                            uniqueRefs[key].append(g)
                        else:
                            uniqueRefs[key] = [g]
                for key in uniqueRefs:
                    # omit lines that have blank 'ref' tags
                    if key is not None and key != 'None':
                        dissolve_feat = cascaded_union(uniqueRefs[key])
                        output.write({'geometry':mapping(dissolve_feat), 'properties': {'ref': key}})



    def split_and_duplicate_segments (self, inFile, outFile):
        # splits and duplicates line segments which have "," or a";" in the 'ref' tag
        with fiona.open(inFile, 'r', encoding='utf-8') as input:
            input_driver = input.driver
            input_crs = input.crs
            input_schema = input.schema.copy()
            with fiona.open(outFile, 'w', driver=input_driver, crs=input_crs, schema=input_schema, encoding='utf-8') as output:
                for item in input:
                    refTag = item['properties']['ref']
                    if refTag is not None and refTag != 'None':
                        feature2Dup = re.split(',|;',refTag)
                        for feature in feature2Dup:
                            item['properties']['ref'] = feature
                            # check and omit any cases where a '<None>' field could have
                            # been created by splitting at a ',' or a ';' which in the 'ref' tag
                            # WASN'T followed by any other string (i.e. 'MA 87; ')
                            if feature is not None and feature != '':
                                output.write(item)


    def create_shield_type(self, item, region):
        refText = item['properties']['ref']
        if region == "USA":
            # find interstates
            interstates_pattern = re.compile(r'^[I](\-|\s).*', re.IGNORECASE)
            interstates_match = interstates_pattern.search(refText)
            # find us_highways
            us_hwys_pattern = re.compile(r'^[U][S](\s|\-).*', re.IGNORECASE)
            us_hwys_match = us_hwys_pattern.search(refText)
            # find state_highways, includes Marshall Islands (MH), Virgin Islands (VI), Puerto Rico (PR), Guam (GU),
            # America Samoa (AS), as well as and highways starting with 'ST', 'SH', and 'SR'
            state_hwys = ['IA', 'KS', 'UT', 'VA', 'NC', 'NE', 'SD', 'AL', 'ID', 'DE', 'AK', 'CT', 'PR', 'NM', 'MS', 'CO', 'NJ', 'FL', 'MN', 'VI', 'NV', 'AZ', 'WI', 'ND', 'PA', 'OK', 'KY', 'RI', 'NH', 'MO', 'ME', 'VT', 'GA', 'GU', 'AS', 'NY', 'CA', 'HI', 'IL', 'TN', 'MA', 'OH', 'MD', 'MI', 'WY', 'WA', 'OR', 'MH', 'SC', 'IN', 'LA', 'DC', 'MT', 'AR', 'WV', 'TX', 'ST', 'SR', 'SH']
            state_hwys_pattern = re.compile(r'\b(' + '|'.join(state_hwys) + r')\b', re.IGNORECASE)
            state_hwys_match = state_hwys_pattern.search(refText)
            if interstates_match is not None:
                shield_text = "I"
                return shield_text
            elif us_hwys_match is not None:
                shield_text = "US"
                return shield_text
            elif state_hwys_match is not None:
                shield_text = "ST"
                return shield_text
        elif region == "Global":
            return "GLOBAL"

    def create_label(self, item, region):
        refText = item['properties']['ref']

        if region == "USA":
            # this series of substitution calls omit particular strings and
            # abbreviate directionals (North,South,East,West)
            # before parsing using the USA label match pattern 
            refText = re.sub(r'Business', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Alternate', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Truck', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Link', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Bypass', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Spur', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Local', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Connector', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Historic', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Alt', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Bus', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Loop', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Scenic', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Ramp', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'Express', '', refText, flags=re.IGNORECASE)
            # deals with US Hwy cases where there is TWO labels for a highway.
            # but no split character
            refText = re.sub(r' US', '', refText, flags=re.IGNORECASE)
            # deals with Interstate cases where there is TWO labels for a highway.
            # but no split character
            refText = re.sub(r' I', '', refText, flags=re.IGNORECASE)
            refText = re.sub(r'North', 'N', refText, flags=re.IGNORECASE)
            refText = re.sub(r'South', 'S', refText, flags=re.IGNORECASE)
            refText = re.sub(r'East', 'E', refText, flags=re.IGNORECASE)
            refText = re.sub(r'West', 'W', refText, flags=re.IGNORECASE)
            # regex group1 explicitly extracts first series of numbers from 'ref'
            # also optionally extracts letters followed by a '-' or a 'space' or nothing.
            # Strings with letters in them must end on a letter.
            # case-insensitive
            usa_label_pattern = re.compile(r'(?im)^\D*(\d+(?:(\w)|[- ][a-z ]*[a-z])?)')
            usa_label_match = usa_label_pattern.search(refText)

            if usa_label_match is not None:
                usa_label = usa_label_match.group(1)

                return usa_label

        elif region == "Global":
            try:

                # remove MEX from ALL global motorway labels
                refText = re.sub(r'MEX\s?\-?', "", refText, flags=re.IGNORECASE)
                # IF there are no numbers in the 'ref' tag REMOVE do not parse into label
                global_label_pattern = re.compile(r'\d+')
                global_label_match = global_label_pattern.search(refText)
                if global_label_match is not None:
                    # for ALL global motorway labels truncate down to 7 characters
                    truncateRef = refText[:7].strip()
                    # re-check that there is at least one numeric character in the
                    # 7 character label
                    label_match = global_label_pattern.search(truncateRef)
                    if label_match is not None:
                        return truncateRef
            except:
                print "there was an error"
                pass


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

def main():
    print "number of arguments (incl. py file name): " + str(len(sys.argv))
    if len(sys.argv) != 4:
        print "Wrong amount of arguments!"
        usage()
        exit()

    inputFile = sys.argv[1]
    tmpFilePath = "temp"
    tmpFilePath_two = "temp2"
    outputFile = sys.argv[2]
    region = sys.argv[3]

    shieldLabelsObject = ShieldLabels()
    print "Dissolving...creating temp file"
    shieldLabelsObject.dissolve(inputFile, tmpFilePath)
    print "Splitting and Duplicating...creating another temp file"
    shieldLabelsObject.split_and_duplicate_segments(tmpFilePath, tmpFilePath_two)
    shieldLabelsObject.process_file(tmpFilePath_two, outputFile, region)

#    shutil.rmtree(tmpFilePath, onerror = on_rm_error)
    print "Finished creating new label lines shapefile! You can now delete all temp files!"

def usage():
    print "python ShieldLabels.py <input file> <output file>"

if __name__ == "__main__":
    main()
