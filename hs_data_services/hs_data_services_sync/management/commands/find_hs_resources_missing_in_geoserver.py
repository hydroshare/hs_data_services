from django.core.management.base import BaseCommand
from hs_data_services_sync import utilities


class Command(BaseCommand):
    help = "Find HS resources that don't have a corresponding workspace in GeoServer"

    def handle(self, *args, **options):
        resources = utilities.get_list_of_public_geo_resources()
        num_resources = len(resources)
        print(f"Found {num_resources} resources in HydroShare")

        # use the geoserver rest api to get a list of workspaces
        geoserver_workspaces = utilities.get_geoserver_workspaces_list()
        num_workspaces = len(geoserver_workspaces)
        print(f"Found {num_workspaces} workspaces in GeoServer")

        # every workspace name has a leading "HS-" string that must be removed
        geoserver_workspaces = [ws["name"][3:] for ws in geoserver_workspaces]

        hs_resources_missing_in_geoserver = []
        for res_id in resources:
            if res_id not in geoserver_workspaces:
                hs_resources_missing_in_geoserver.append(res_id)
        num_missing_resources = len(hs_resources_missing_in_geoserver)
        print(f"Found {num_missing_resources} resources missing in GeoServer")

        # Now list all of the Geo aggregations in the missing resources
        # So that we can compare them with the layers in GeoServer
        print("Now listing all Geo aggregations in the missing resources")
        count = 1
        total_missing_layers = 0
        for res_id in hs_resources_missing_in_geoserver:
            print("*" * 80)
            print(f"{count}/{num_missing_resources} - Resource {res_id}")
            database_list = utilities.get_database_list(
                res_id=res_id,
            )
            if database_list['access'] == 'public':
                dbs = database_list['geoserver']['register']
                num_dbs = len(dbs)
                if num_dbs == 0:
                    print(f"Resource {res_id} has no Geo aggregations")
                else:
                    print(f"Resource {res_id} has {num_dbs} Geo aggregations")
                    for db in dbs:
                        print(f"Resource {res_id} has a {db['layer_type']}: {db['hs_path']}")
                    total_missing_layers += num_dbs
            count += 1
            print()
        print("-" * 80)
        print(f"Found {num_missing_resources} resources missing in GeoServer")
        print(f"Found {total_missing_layers} Geo aggregations missing in GeoServer")
        print("Search complete")
