from django.core.management.base import BaseCommand
from hs_data_services_sync import utilities


class Command(BaseCommand):
    help = "Unregister resource in GeoServer"

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        resource_ids = options['resource_ids']
        if len(resource_ids) > 0:
            for resource_id in resource_ids:
                print(f"Unregistering resource: {resource_id}")
                result = utilities.unregister_geoserver_databases(resource_id)
                print(result)
        else:
            resources = utilities.get_list_of_public_geo_resources()
            num_resources = len(resources)
            print(f"Unregistering {num_resources} public resources")
            counter = 1
            for res_id in resources:
                print(f"{counter}/{num_resources} - Unregistering: {res_id}")
                result = utilities.unregister_geoserver_databases(res_id)
                print(result)
                counter += 1
        print("Done unregistering resources")
