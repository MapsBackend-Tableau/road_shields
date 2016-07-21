"""The purpose of this script is to create road shields based based on an input road network.

The road network should contain a single unique label for each line segment. The pre-process
step creates a file of spaced nodes (based on the input parameter) for every segment in the
file. The post-process step takes the list of input nodes and removes any nodes within the
supplied radius that contain a value identical to surrounding nodes based on the supplied
group field.

An example is the following:

    input_file = r"D:\work\osm_motorways\osm_world_labels.shp"
    output_file = r"D:\work\osm_motorways\osm_world_label_nodes_2000.shp"
    complete_file = r"D:\work\osm_motorways\osm_world_label_points_6000.shp"

    LineTools.add_nodes(input_file=input_file, output_file=output_file, interval=2000)
    LineTools.thin_nodes(input_file=output_file, output_file=complete_file, group_field='label', radius=6000)

In the above example, an input file of line segments 'osm_world_labels.shp', is processed using an interval
of 2000. The interval means a point will be placed every 2000 meters (as the input projection is based on
meters) and written to an output file called 'osm_world_label_nodes_2000.shp'.

The resulting node file 'osm_world_label_nodes_2000.shp' is then used in the thin_nodes process whereby
nodes with the same 'label' within 6000 meters are removed from the file.

.. moduleauthor:: Ian Erickson <ierickson@tableausoftware.com>
"""

import fiona
import time
from shapely.geometry import shape, mapping



class LineTools:
    """A class to provide line processing tools.

    All utility methods are defined as static and therefore an instance of the class is never created.
    """

    def __init__(self):
        return

    @staticmethod
    def add_nodes(input_file, output_file, interval=1000):
        """Creates a shapefile of node content based on an input file of lines.

        :param input_file: The input shapefile containing line features.
        :type input_file: str.
        :param output_file: The output shapefile that will contain point features.
        :type output_file: str.
        :param interval: The interval (in projected units) for nodes created from lines.
        :type interval: int.
        :returns: None.

        """
        with fiona.open(input_file, 'r', encoding='utf-8') as f_input:
            source_driver = f_input.driver
            source_crs = f_input.crs
            source_schema = f_input.schema

            source_schema['geometry'] = 'Point'
            props = dict(source_schema['properties'])
            props.update({'INCLUDE': 'str:1'})
            props.update({'PROCESSED': 'str:1'})
            source_schema['properties'] = props

            f_output = fiona.open(output_file,
                                  'w',
                                  driver=source_driver,
                                  crs=source_crs,
                                  schema=source_schema, encoding='utf-8')

            for rec in f_input:
                geom = shape(rec['geometry'])
                if geom is None:
                    continue

                d = 0
                r = dict(rec['properties'])
                r['INCLUDE'] = 'Y'
                r['PROCESSED'] = 'N'

                while d < geom.length:
                    f_output.write({'geometry': mapping(geom.interpolate(d)), 'properties': r})
                    d += interval

            f_output.close()
        return

    @staticmethod
    def thin_nodes(input_file, output_file, group_field, radius=4000):
        """Thins a file of point objects sharing a common field value within a supplied radius.

        :param input_file: The input shapefile containing point features.
        :type input_file: str.
        :param output_file: The output shapefile that will contain thinned (non-duplicate) point features.
        :type output_file: str.
        :param group_field: The field in the shapefile that specifies the group.
        :type group_field: str.
        :param radius: The radius (in projected units) in which duplicate nodes will be removed.
        :type radius: int.
        :returns: None.

        """
        recs = None
        with fiona.open(input_file, encoding='utf-8') as f_input:
            source_driver = f_input.driver
            source_crs = f_input.crs
            source_schema = f_input.schema

            print("Loading records into memory...")
            recs = list(f_input)
            print("{0} records loaded.".format(len(recs)))

            start_time = time.time()
            for x in range(len(recs)):
                if x % 100 == 0 and x != 0:
                    block_time = time.time()
                    estimate = (len(recs) - x) / (x / (block_time - start_time))
                    print("Processing record #{0}. Estimated completion: {1} seconds...".format(x, estimate))

                active_rec = recs[x]

                if active_rec['properties']['INCLUDE'] == 'N' or active_rec['properties']['PROCESSED'] == 'Y':
                    continue

                geom = shape(active_rec['geometry'])
                if geom is None:
                    active_rec['properties']['INCLUDE'] = 'N'
                    active_rec['properties']['PROCESSED'] = 'Y'
                    continue

                search_ids = LineTools.records_within(input_file=input_file, obj=geom.buffer(radius * 1.1, 100))
                geom_buffer = geom.buffer(radius, 100)
                for search_id in search_ids:
                    search_rec = recs[int(search_id)]

                    if shape(search_rec['geometry']).within(geom_buffer):
                        if int(active_rec['id']) != int(search_rec['id']) and search_rec['id'] == search_id and active_rec['properties'][group_field] == search_rec['properties'][group_field] and search_rec['properties']['INCLUDE'] == 'Y' and active_rec['properties']['PROCESSED'] == 'N':
                            search_rec['properties']['INCLUDE'] = 'N'
                            search_rec['properties']['PROCESSED'] = 'Y'

                active_rec['properties']['INCLUDE'] = 'Y'
                active_rec['properties']['PROCESSED'] = 'N'

            print("Writing output file...")
            with fiona.open(output_file,
                            'w',
                            driver=source_driver,
                            crs=source_crs,
                            schema=source_schema, encoding='utf-8') as f_output:
                for r in recs:
                    if r['properties']['INCLUDE'] == 'Y':
                        f_output.write(r)

        return

    @staticmethod
    def records_within(input_file, obj):
        """Returns a list of records in the input_file that are within the supplied object.

        :param input_file: The input shapefile containing point features.
        :type input_file: str.
        :param obj: The geometry object that provides the spatial extent of the search.
        :type obj: shape.
        :returns: A list of records within the bounds of the supplied shape.

        """
        recs = []
        with fiona.open(input_file, encoding='utf-8') as f_input:
            f_input.filter(obj.bounds)

            for rec in f_input:
                recs.append(rec['id'])

        return recs


if __name__ == '__main__':

     input_file = r"I:\It_26\116609_Regenerate_Global_HWY_shields\input_file\osm_motorways_global_shield_finallines.shp"
     complete_file = r"I:\It_26\116609_Regenerate_Global_HWY_shields\complete_file\osm_global_shields_8000.shp"
     output_file = r"I:\It_26\116609_Regenerate_Global_HWY_shields\complete_file\osm_global_shields_4000.shp"

     #LineTools.add_nodes(input_file=input_file, output_file=output_file, interval=2000)
     LineTools.thin_nodes(input_file=output_file, output_file=complete_file, group_field='label', radius=4000)
