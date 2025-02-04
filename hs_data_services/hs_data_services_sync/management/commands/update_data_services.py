from django.core.management.base import BaseCommand
from hs_data_services_sync import tasks
from hs_data_services_sync.utilities import get_list_of_public_geo_resources


class Command(BaseCommand):
    help = "Update data services for a resource or all public resources"

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        resource_ids = options['resource_ids']
        if len(resource_ids) > 0:
            for resource_id in resource_ids:
                print(f"Updating services for resource: {resource_id}")
                result = tasks.update_data_services_task(resource_id)
                print(result)
        else:
            resources = get_list_of_public_geo_resources()
            num_resources = len(resources)
            print(f"Updating resources for {num_resources} resources")
            counter = 1
            for res_id in resources:
                print(f"{counter}/{num_resources} - Updating services for resource: {res_id}")
                result = tasks.update_data_services_task(res_id)
                print(result)
                counter += 1
        print("Done updating data services")
