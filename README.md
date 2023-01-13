# HydroShare Data Services

This application manages HydroShare web data services by registering resource content on systems like GeoServer and HydroServer. It has been designed to support HydroShare data service capabilities by linking HydroShare data to data servers in real time.

## Getting Started

These instructions will help you install and run this application in a production environment.

### Prerequisites

##### Docker:
* [Install Docker Engine](https://docs.docker.com/install/)

### Installing

##### Edit Django settings (for prod):

For local development, skip this step and use the local_settings.py file that exists in this repo.

Copy hs_data_services/hs_data_services/hs_data_services/local_settings.template to overwrite local_settings.py.

Edit the following settings in local_settings.py:
* {{HYDROSHARE_DOMAIN}}     - The domain for the connected HydroShare instance e.g. 'hydroshare.org'
* {{SECRET_KEY}}            - A secret key for the Django app. (https://miniwebtool.com/django-secret-key-generator/)
* {{DATA_SERVICES_URL}}     - The data services URL e.g. 'https://geoserver.hydroshare.org/his'
* {{HYDROSHARE_REST_URL}}   - HydroShare's REST URL e.g. 'https://www.hydroshare.org/hsapi'
* {{GEOSERVER_REST_URL}}    - GeoServer's REST URL e.g. 'https://geoserver.hydroshare.org/geoserver/rest'
* {{GEOSERVER_USERNAME}}    - Username for GeoServer. Default is 'admin'
* {{GEOSERVER_PASSWORD}}    - Password for GeoServer. Default is 'geoserver'. Change in production.
* {{IRODS_LOCAL_DIRECTORY}} - Local GeoServer path to iRODS data. Typically somewhere in /projects
* {{WORKSPACE_PREFIX}}      - Resource ID prefix for GeoServer workspaces; this must begin with a letter. e.g. 'HS'

##### Edit Docker settings:

For local development, skip this step and use the .env values that exist in this repo.

Edit the following settings in hs_data_services/docker-compose.yml

* {{IRODS_ACCESS_UID}}      - The UID of a user on the host system with iRODS read access.
* {{HYDROSHARE_DOMAIN}}     - The domain for the connected HydroShare instance e.g. 'hydroshare.org'

##### Start Docker containers (for non-local builds):

From hs_data_services directory, run the following command to build Docker images:
```
$ sudo docker-compose build
```

Run the following command to run the Docker containers:
```
$ sudo docker-compose up -d
```

By default, all services will be exposed locally on port 8000 and static files will be located in /static/his/. 

##### OR Start Docker containers (for local dev):

Ensure that Hydroshare is up and running locally on port 8000

From hs_data_services directory:
`UID=${UID} docker-compose build`
`UID=${UID} docker-compose up -d`

Services will be exposed locally on DATA_SERVICES_PORT (default 8090), for example: http://localhost:8090/his/admin/

HSWS_URL = "http://host.docker.internal:8080/his/services/update"
HSWS_API_TOKEN = "fba02c9f6e9a0c269681ece8bd330a9c314923f3"
HSWS_TIMEOUT = 10
HSWS_PUBLISH_URLS = True
HSWS_ACTIVATED = True

HSWS_GEOSERVER_URL = "http://host.docker.internal:8080/geoserver"
HSWS_GEOSERVER_ESCAPE = {
    '/': ' '
}

##### Post-Installation steps:

Log in to the Django site at {host_url}/his/admin with default username and password: 'admin' and 'default'
From the admin settings page, change the admin password.
Create a new authentication token by clicking 'add' under 'Auth Token'. Select 'admin' from the dropdown and click save. Note the newly created token value.

Log in to GeoServer at {host_url}/geoserver/web with default username and password: 'admin' and 'geoserver'
From the main page, change the admin password. This should match the GEOSERVER_PASSWORD setting from earlier.
In Global Settings, change the Proxy Base URL to '{host_url}/geoserver'. This will ensure that page navigation is working properly on the GeoServer web site.
From this site, you may also update the contact information provided by GeoServer.
You may also wish to remove the existing test content by deleting their workspaces. Be aware that if you do this, you must set up a default workspace (such as 'hydroshare'), or the next workspace created will be made the default workspace.

Update or add the following settings to HydroShare:
* HSWS_URL                  - '{host_url}/his/services/update'
* HSWS_API_TOKEN            - This is the Django authentication token you created earlier.
* HSWS_TIMEOUT              - This can be fairly short e.g. 10
* HSWS_ACTIVATED            - True or False

Once everything is set up, HydroShare should start sending update requests to this data services app. You can check that this app is receiving those requests by going to {host_url}/flower and clicking on 'Tasks'. You can test it manually by sending a POST request to {host_url}/his/services/update/{resource_id}/ and adding {'Authorization': 'Token HSWS_API_TOKEN'} to the request's headers.

##### Troubleshooting steps:

After following the instructions above, if GeoServer isn't working as expected, try the following steps:

1. Check {host_url}/flower to make sure the server is receiving resource registration requests from HydroShare. Under the 'tasks' tab there should be an update_data_services_task for each request received from HydroShare. If these tasks aren't appearing, there's a communication issue between HydroShare and this service. This could be due to the HydroShare HSWS settings not being correct, or an issue with the GeoServer NGINX setup.

2. You can rule out other issues by manually sending a registration request to GeoServer. Make sure the resource you want to test is ready and made public. Use register_resource_test.ipynb to manually send an update request to this service. After sending the request, if you still don't see an update_data_services_task, double check your URLs and authentication token settings on HydroShare. If you see the task and the layers are visible on the GeoServer layer preview page, there's a HydroShare communication issue, but everything else is working. If the layers are not visible on GeoServer, there's an issue with the GeoServer setup.

3. Through the GeoServer UI, you can try manually creating a GeoServer layer. From the GeoServer main page, log in and click 'Stores' and then 'Add new Store'. Click 'Shapefile' or 'GeoTIFF', depending on what type of layer you're testing. From there, click 'Browse' under 'Connection Parameters'. Select '/' from the dropdown, and you should see 'projects' in the directory (or the name of the volume you mounted into the container). From there, you should be able to navigate to your shapefile or GeoTIFF (you'll need to know where it is). If a directory appears empty when you know there's data in it, there's a permissions issue with the volume and the GeoServer user does not have permission to read that directory. You'll need to make sure the GeoServer user ID you picked earlier matches the user ID of a user on the host that has full read access to your resource data. If you're able to navigate to the file, try creating a new store. If you encounter any error while trying to create the store, there's likely an issue with the data file that needs to be resolved.

4. If there appears to be a permissions issue, you can enter the GeoServer Docker container using `sudo docker exec -it {container_name} /bin/bash` and check the permissions of the mounted volume.

## Built With

* [Docker](https://docs.docker.com) - Docker Engine
* [Django](https://www.djangoproject.com) - Python Web Framework
* [Gunicorn](https://gunicorn.org) - WSGI HTTP Server
* [GeoServer](http://geoserver.org) - Geospatial Data Server

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details