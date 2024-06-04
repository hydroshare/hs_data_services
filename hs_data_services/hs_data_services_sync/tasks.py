from celery import task
from celery.utils.log import get_task_logger
from hs_data_services_sync import utilities

logger = get_task_logger(__name__)


@task(name='update_data_services_task')
def update_data_services_task(resource_id):
    """
    Update data services.
    """

    response = utilities.update_data_services(resource_id)

    return True
