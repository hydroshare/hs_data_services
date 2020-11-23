from celery import task
from hs_data_services_sync import utilities


@task(name='update_data_services_task')
def update_data_services_task(resource_id):
    """
    Update data services.
    """

    response = utilities.update_data_services(resource_id)

    return True
