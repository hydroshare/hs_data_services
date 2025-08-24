from django.core.management.base import BaseCommand
from hs_data_services_sync import utilities
from hs_data_services import settings


class Command(BaseCommand):
    help = "Find HS aggregations that don't have a corresponding layer in GeoServer"

    def handle(self, *args, **options):
        hydroshare_url = settings.HYDROSHARE_URL
        hydroshare_url = hydroshare_url.replace("hsapi", "resource")
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
            files_missing_for_this_res = []

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
                if (raster["layer_name"].replace("/", " "), 'coveragestores') not in geoserver_rasters:
                    files_missing_for_this_res.append(raster)
            for feature in feature_files:
                geoserver_features = [gs for gs in geoserver_list if gs[1] == 'datastores']
                if (feature["layer_name"].replace("/", " "), 'datastores') not in geoserver_features:
                    files_missing_for_this_res.append(feature)
            num_files_missing = len(files_missing_for_this_res)
            if num_files_missing > 0:
                total_missing_layers += num_files_missing
                hs_aggregations_missing_in_geoserver.append((res_id, files_missing_for_this_res))
            else:
                print(f"Resource {res_id} has all files registered in GeoServer")
            res_count += 1
        print("-" * 80)
        for res_id, files in hs_aggregations_missing_in_geoserver:
            print("*" * 80)
            print(f"Resource {res_id} has the following missing files in GeoServer: ")
            for file in files:
                print(f"{hydroshare_url}/{file['hs_path']}")
        print("-" * 80)
        print("Search complete!")
        print(f"Found {len(hs_aggregations_missing_in_geoserver)} resources with missing layers")
        print(f"Found {total_missing_layers} total layers missing in GeoServer")
