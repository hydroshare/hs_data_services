import requests
import json
from django.core.management.base import BaseCommand
from hs_data_services import settings
from hs_data_services_sync import tasks


class Command(BaseCommand):
    help = "Copy resource files from HydroShare to geoserver storage"

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        resource_ids = options['resource_ids']
        if len(resource_ids) > 0:
            for resource_id in resource_ids:
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
        hydroshare_url = "/".join(settings.HYDROSHARE_URL.split("/")[:-1])
        types = ["Geographic Feature (ESRI Shapefiles)", "Geographic Raster"]
        # replace spaces with + for the query string
        types = [t.replace(" ", "+") for t in types]
        params = {
            "type": types,
            "availability": ["public"],
            "geofilter": "false"
        }
        rest_url = f"{hydroshare_url}/discoverapi/?filter={json.dumps(params)}"
        rest_url = rest_url.replace(" ", "")
        print(f"Getting list of public geospatial resources from: {rest_url}")
        response = requests.get(rest_url)
        response_json = response.json()
        page_count = response_json.get('pagecount', 0)
        rescount = response_json.get('rescount', 0)
        perpage = response_json.get('perpage', 0)
        res_ids = []
        print(f"Iterating over {page_count} pages of {perpage} resources each, total resources: {rescount}")
        for i in range(1, page_count):
            print(f"Getting page {i}")
            response = requests.get(f"{rest_url}&pnum={i}")
            response_json = response.json()
            resources = json.loads(response_json.get('resources', []))
            new_ids = [resource["short_id"] for resource in resources if resource.get('short_id', None)]
            res_ids.extend(new_ids)
        print(f"Found {len(res_ids)} public geospatial resources")
        print(f"Should match {rescount}")
        return res_ids

    def copy_files(self, resource_id):
        return tasks.update_data_services_task.delay(resource_id)
