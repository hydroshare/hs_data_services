from django.core.management.base import BaseCommand
from hs_data_services_sync import utilities
from hsclient import HydroShare

hs = HydroShare()


class Command(BaseCommand):
    help = "Find HS aggregations that don't have a corresponding layer in GeoServer"

    def handle(self, *args, **options):
        resources = utilities.get_list_of_public_geo_resources()
        num_resources = len(resources)
        print(f"Found {num_resources} resources in HydroShare")

        # for every hydroshare resource, get a list of its geo aggregations
        # and compare them with the layers in geoserver
        hs_aggregations_missing_in_geoserver = []

        res_count = 1
        for res_id in resources:
            print(f"{res_count}/{num_resources} - Resource {res_id}")
            aggs_missing_for_this_res = []
            res = hs.resource(res_id)
            raster_aggs = res.aggregations(type="GeoRaster")
            feature_aggs = res.aggregations(type="GeoFeature")
            if len(raster_aggs) == 0 and len(feature_aggs) == 0:
                print(f"Resource {res_id} has no Geo aggregations")
                res_count += 1
                continue
            geoserver_list = utilities.get_geoserver_list(res_id)
            for raster in raster_aggs:
                print(f"Resource {res_id} has a {raster.metadata.type}: {raster.metadata.title}")
                # check if the raster aggregation is in geoserver
                # geoserver_list is a list of tupples, extract those that are 'coveragestores'
                geoserver_rasters = [gs for gs in geoserver_list if gs[1] == 'coveragestores']
                if (raster.metadata.title, 'coveragestores') not in geoserver_rasters:
                    aggs_missing_for_this_res.append(raster.metadata.title)
            for feature in feature_aggs:
                print(f"Resource {res_id} has a {feature.metadata.type}: {feature.metadata.title}")
                # check if the feature aggregation is in geoserver
                # geoserver_list is a list of tupples, extract those that are 'datastores'
                geoserver_features = [gs for gs in geoserver_list if gs[1] == 'datastores']
                if (feature.metadata.title, 'datastores') not in geoserver_features:
                    aggs_missing_for_this_res.append(feature.metadata.title)
            if len(aggs_missing_for_this_res) > 0:
                hs_aggregations_missing_in_geoserver.append((res_id, aggs_missing_for_this_res))
                print(f"Resource {res_id} has {len(aggs_missing_for_this_res)} aggregations missing in GeoServer: ")
                for agg in aggs_missing_for_this_res:
                    print(agg)
            else:
                print(f"Resource {res_id} has all aggregations registered in GeoServer")
            res_count += 1
        print("-" * 80)
        print(f"Found {len(hs_aggregations_missing_in_geoserver)} resources with missing aggregations in GeoServer")
        for res_id, aggs in hs_aggregations_missing_in_geoserver:
            print(f"Resource {res_id} has the following missing aggregations in GeoServer: ")
            for agg in aggs:
                print(agg)
        print("Search complete")
