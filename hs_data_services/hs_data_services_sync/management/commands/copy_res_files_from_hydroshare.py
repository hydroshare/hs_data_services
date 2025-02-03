from django.core.management.base import BaseCommand
from hs_data_services_sync import tasks
from hs_data_services_sync.utilities import get_list_of_public_geo_resources


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
            resources = get_list_of_public_geo_resources()
            num_resources = len(resources)
            print(f"Copying files from {num_resources} resources")
            counter = 1
            for res_id in resources:
                print(f"{counter}/{num_resources} - Copying files from resource: {res_id}")
                result = self.copy_files(res_id)
                print(result)
                counter += 1
        print("Done copying files")

    def copy_files(self, resource_id):
        return tasks.update_data_services_task.delay(resource_id)
