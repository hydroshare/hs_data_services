from django.core.management.base import BaseCommand
from hs_data_services_sync.utilities import get_list_of_public_geo_resources, get_geoserver_workspaces_list


class Command(BaseCommand):
    help = "Find HS resources that don't have a corresponding workspace in GeoServer"

    def handle(self, *args, **options):
        resources = get_list_of_public_geo_resources()
        num_resources = len(resources)
        print(f"Found {num_resources} resources in HydroShare")

        # use the geoserver rest api to get a list of workspaces
        geoserver_workspaces = get_geoserver_workspaces_list()
        num_workspaces = len(geoserver_workspaces)
        print(f"Found {num_workspaces} workspaces in GeoServer")

        # every workspace name has a leading "HS-" string that must be removed
        geoserver_workspaces = [ws_name[3:] for ws_name in geoserver_workspaces]

        hs_resources_missing_in_geoserver = []
        for res_id in resources:
            if res_id not in geoserver_workspaces:
                hs_resources_missing_in_geoserver.append(res_id)
                print(f"Resource {res_id} is missing in GeoServer")

        num_missing_resources = len(hs_resources_missing_in_geoserver)
        print(f"Found {num_missing_resources} resources missing in GeoServer")
        print("Done finding resources missing in GeoServer")
