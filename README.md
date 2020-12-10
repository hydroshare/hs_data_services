# HydroShare Data Services

This application manages HydroShare web data services by registering resource content on systems like GeoServer and HydroServer. It has been designed to support HydroShare data service capabilities by linking HydroShare data to data servers in real time.

## Getting Started

These instructions will help you install and run this application in a production environment.

### Prerequisites

##### Docker:
* [Install Docker Engine](https://docs.docker.com/install/)

### Installing

##### Edit Django settings:

Rename hs_data_services/hs_data_services/hs_data_services/local_settings.template to local_settings.py.

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

Edit the following settings in hs_data_services/docker-compose.yml

* {{IRODS_ACCESS_UID}}      - The UID of a user on the host system with iRODS read access.
* {{HYDROSHARE_DOMAIN}}     - The domain for the connected HydroShare instance e.g. 'hydroshare.org'

##### Start Docker containers:

From hs_data_services directory, run the following command to build Docker images:
```
$ sudo docker-compose build
```

Run the following command to run the Docker containers:
```
$ sudo docker-compose up -d
```

By default, all services will be exposed locally on port 8000 and static files will be located in /static/his/. 

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

## Built With

* [Docker](https://docs.docker.com) - Docker Engine
* [Django](https://www.djangoproject.com) - Python Web Framework
* [Gunicorn](https://gunicorn.org) - WSGI HTTP Server
* [GeoServer](http://geoserver.org) - Geospatial Data Server

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details