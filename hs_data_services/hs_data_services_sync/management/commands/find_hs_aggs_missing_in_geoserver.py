from django.core.management.base import BaseCommand
from hs_data_services_sync import utilities
from hsclient import HydroShare


class Command(BaseCommand):
    help = "Find HS aggregations that don't have a corresponding layer in GeoServer"

    def handle(self, *args, **options):
        resources = utilities.get_list_of_public_geo_resources()
        num_resources = len(resources)
        print(f"Found {num_resources} resources in HydroShare")

        # for every hydroshare resource, get a list of its geo aggregations
        # and compare them with the layers in geoserver
        hs_aggregations_missing_in_geoserver = []
        total_missing_layers = 0

        res_count = 1
        for res_id in resources:
            print(f"{total_missing_layers} total layers missing and {len(hs_aggregations_missing_in_geoserver)} resources so far...")
            print(f"{res_count}/{num_resources} - Resource {res_id}")
            aggs_missing_for_this_res = []

            # get the files list for this resource
            file_list = utilities.get_database_list(res_id, ignore_already_registered=True)["geoserver"]["register"]
            raster_files = [f for f in file_list if f["layer_type"] == 'GeographicRaster']
            feature_files = [f for f in file_list if f["layer_type"] == 'GeographicFeature']
            if len(raster_files) == 0 and len(raster_files) == 0:
                print(f"Resource {res_id} has no Geo aggregations")
                res_count += 1
                continue
            geoserver_list = utilities.get_geoserver_list(res_id)
            for raster in raster_files:
                geoserver_rasters = [gs for gs in geoserver_list if gs[1] == 'coveragestores']
                if (raster["layer_name"], 'coveragestores') not in geoserver_rasters:
                    aggs_missing_for_this_res.append(raster)
            for feature in feature_files:
                geoserver_features = [gs for gs in geoserver_list if gs[1] == 'datastores']
                if (feature["layer_name"], 'datastores') not in geoserver_features:
                    aggs_missing_for_this_res.append(feature)
            num_aggs_missing = len(aggs_missing_for_this_res)
            if num_aggs_missing > 0:
                total_missing_layers += num_aggs_missing
                hs_aggregations_missing_in_geoserver.append((res_id, aggs_missing_for_this_res))
            else:
                print(f"Resource {res_id} has all aggregations registered in GeoServer")
            res_count += 1
        print("-" * 80)
        for res_id, aggs in hs_aggregations_missing_in_geoserver:
            print("*" * 80)
            print(f"Resource {res_id} has the following missing aggregations in GeoServer: ")
            for agg in aggs:
                print(agg)
        print("-" * 80)
        print("Search complete!")
        print(f"Found {len(hs_aggregations_missing_in_geoserver)} resources with missing layers")
        print(f"Found {total_missing_layers} total layers missing in GeoServer")
