import requests
from django.core.management.base import BaseCommand
from hs_data_services import settings
from hs_data_services_sync import tasks


class Command(BaseCommand):
    help = "Copy resource files from HydroShare to geoserver storage"

    def add_arguments(self, parser):
        parser.add_argument('resource_id', type=str, help='The HydroShare resource ID to copy files from')

    def handle(self, *args, **options):
        resource_id = options.get('resource_id')
        if resource_id:
            print(f"Copying files from resource: {resource_id}")
            result = self.copy_files(resource_id)
            print(result)
        else:
            resources = self.get_list_of_public_geo_resources()
            num_resources = len(resources)
            print(f"Copying files from {num_resources} resources")
            counter = 1
            for res_id in resources:
                print(f"{counter}/{num_resources} - Copying files from resource: {res_id}")
                result = self.copy_files(res_id)
                print(result)
                counter += 1
        print("Done copying files")

    def get_list_of_public_geo_resources(self):
        hydroshare_url = settings.HYDROSHARE_URL
        params = {
          "filter": {
            "type": ["Geographic Feature (ESRI Shapefiles)", "Geographic Raster"],
            "availability": ["public"],
            "geofilter": False
          }
        }
        rest_url = f"{hydroshare_url}/discoverapi/?filter={params}"
        response = requests.get(rest_url)
        response_json = response.json()
        resources = response_json.get('resources', [])
        res_ids = [resource.short_id for resource in resources if resource.get('short_id', None)]
        return res_ids

    def copy_files(self, resource_id):
        return tasks.update_data_services_task.delay(resource_id)
