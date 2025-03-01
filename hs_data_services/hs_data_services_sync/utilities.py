import logging
import requests
import json
import os
import shutil
import urllib
from hs_data_services import settings
from lxml import etree

logger = logging.getLogger(__name__)


def update_data_services(resource_id):
    """
    Update data services registration for a HydroShare resource.
    """

    logger.info(f"Updating data services for resource: {resource_id}")
    response = {
        'success': False,
        'message': None,
        'content': None
    }

    database_list = get_database_list(
        res_id=resource_id
    )

    if database_list['access'] == 'public':
        if database_list['geoserver']['create_workspace']:
            register_geoserver_workspace(resource_id)

        for db in database_list['geoserver']['unregister']:
            unregister_geoserver_db(resource_id, db)

        for db in database_list['geoserver']['register']:
            # copy geoserver files from HS to GeoServer
            file_transfer_info = copy_files_to_geoserver(resource_id, db)
            if file_transfer_info['success'] is False:
                response['message'] = file_transfer_info['message']
                return response
            db_info = register_geoserver_db(resource_id, db)
            if db_info['success'] is False:
                unregister_geoserver_db(resource_id, db)

        geoserver_list = get_geoserver_list(resource_id)

        if not geoserver_list:
            logging.info("No GeoServer layers found. Unregistering workspace...")
            unregister_geoserver_databases(resource_id)
            remove_files_for_entire_resource(resource_id)

    else:
        logging.info("Resource is private. Unregistering GeoServer databases...")
        unregister_geoserver_databases(resource_id)
        remove_files_for_entire_resource(resource_id)

        response['success'] = True
        response['message'] = f'Successfully unregistered GeoServer data services for resource: {resource_id}'

    logger.info(f"Completed attempt to update data services for resource: {resource_id}")
    return response


def get_database_list(res_id):
    """
    Gets a list of HydroShare databases on which web services can be published.
    """

    logger.info(f"Getting database list for resource: {res_id}")
    db_list = {
        "access": None,
        "geoserver": {
            "create_workspace": True,
            "register": [],
            "unregister": []
        }
    }

    hydroshare_url = settings.HYDROSHARE_URL
    rest_url = f"{hydroshare_url}/resource/{res_id}/file_list/"
    response = requests.get(rest_url)

    if response.status_code != 200:
        db_list["access"] = "private"
        return db_list
    else:
        db_list["access"] = "public"

    file_list = json.loads(response.content.decode('utf-8'))["results"]

    geoserver_list = get_geoserver_list(res_id)
    if geoserver_list:
        db_list["geoserver"]["create_workspace"] = False

    registered_list = []

    for result in file_list:
        if (
               result["logical_file_type"] == "GeoRasterLogicalFile" and 
               result["content_type"] == "image/tiff" and 
               settings.DATA_SERVICES.get("geoserver", {}).get('URL') is not None
           ) or (
               result["logical_file_type"] == "GeoFeatureLogicalFile" and 
               result["content_type"] == "application/x-qgis" and
               settings.DATA_SERVICES.get("geoserver", {}).get('URL') is not None
           ):

            layer_name = '.'.join('/'.join(result['url'].split('/')[7:]).split('.')[:-1])
            layer_path = "/".join(result["url"].split("/")[4:])
            file_name = '.'.join(result['file_name'].split('.')[:-1])
            layer_ext = result["url"].split("/")[-1].split(".")[-1]
            layer_type = result["content_type"]
            if result["content_type"] == "image/tiff" and layer_ext == "tif":
                registered_list.append(layer_name.replace("/", " "))
                if layer_name.replace("/", " ") not in [i[0] for i in geoserver_list]:
                    db_list["geoserver"]["register"].append(
                        {
                            "layer_name": layer_name,
                            "layer_type": "GeographicRaster",
                            "file_name": file_name,
                            "file_type": "geotiff",
                            "hs_path": layer_path,
                            "store_type": "coveragestores",
                            "layer_group": "coverages",
                            "verification": "coverage"
                        }
                    )
            if result["content_type"] == "application/x-qgis" and layer_ext == "shp":
                registered_list.append(layer_name.replace("/", " "))
                if layer_name.replace("/", " ") not in [i[0] for i in geoserver_list]:
                    # get the associated .shx, .dbf, and .prj files
                    extensions = [".shx", ".dbf", ".prj"]
                    associated_files = []
                    for ext in extensions:
                        expected_url = result["url"].replace(".shp", ext)
                        logger.info(f"Checking for associated file: {expected_url}")
                        if expected_url in [i["url"] for i in file_list]:
                            associated_files.append(
                                "/".join(expected_url.split("/")[4:])
                            )
                    db_list["geoserver"]["register"].append(
                        {
                            "layer_name": layer_name,
                            "layer_type": "GeographicFeature",
                            "file_name": file_name,
                            "file_type": "shp",
                            "hs_path": layer_path,
                            "store_type": "datastores",
                            "layer_group": "featuretypes",
                            "verification": "featureType",
                            "associated_files": associated_files,
                        }
                    )

    for layer in geoserver_list:
        if layer[0] not in registered_list:
            db_list["geoserver"]["unregister"].append(
                {
                    "layer_name": layer[0],
                    "store_type": layer[1]
                }
            )

    if not db_list["geoserver"]["register"]:
        db_list["geoserver"]["create_workspace"] = False

    return db_list


def get_geoserver_list(res_id):
    """
    Gets a list of data stores and coverages from a GeoServer workspace.
    """

    logger.info(f"Getting geoserver list for resource: {res_id}")
    layer_list = []

    geoserver_namespace = settings.DATA_SERVICES.get("geoserver", {}).get('NAMESPACE')
    geoserver_url = settings.DATA_SERVICES.get("geoserver", {}).get('URL')
    geoserver_user = settings.DATA_SERVICES.get("geoserver", {}).get('USER')
    geoserver_pass = settings.DATA_SERVICES.get("geoserver", {}).get('PASSWORD')
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    ds_rest_url = f"{geoserver_url}/workspaces/{workspace_id}/datastores.json"
    cv_rest_url = f"{geoserver_url}/workspaces/{workspace_id}/coverages.json"
    ds_response = requests.get(ds_rest_url, auth=geoserver_auth, headers=headers)
    cv_response = requests.get(cv_rest_url, auth=geoserver_auth, headers=headers)

    if ds_response.status_code == 200:
        ds_response_content = json.loads(ds_response.content)
        if ds_response_content.get("dataStores") and ds_response_content.get("dataStores") != "":
            for datastore in ds_response_content["dataStores"]["dataStore"]:
                layer_list.append((datastore["name"], "datastores"))

    if cv_response.status_code == 200:
        cv_response_content = json.loads(cv_response.content)
        if cv_response_content.get("coverages") and cv_response_content.get("coverages") != "":
            for coverage in cv_response_content["coverages"]["coverage"]:
                layer_list.append((coverage["name"], "coveragestores"))

    return layer_list


def register_geoserver_workspace(res_id):
    """
    Add GeoServer workspace.
    """

    logger.info(f"Registering GeoServer workspace for resource: {res_id}")
    geoserver_namespace = settings.DATA_SERVICES.get("geoserver", {}).get('NAMESPACE')
    geoserver_url = settings.DATA_SERVICES.get("geoserver", {}).get('URL')
    geoserver_user = settings.DATA_SERVICES.get("geoserver", {}).get('USER')
    geoserver_pass = settings.DATA_SERVICES.get("geoserver", {}).get('PASSWORD')
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    unregister_geoserver_databases(res_id)

    headers = {
        "content-type": "application/json"
    }

    data = json.dumps({"workspace": {"name": workspace_id}})
    rest_url = f"{geoserver_url}/workspaces"
    response = requests.post(rest_url, headers=headers, data=data, auth=geoserver_auth)

    return workspace_id


def unregister_geoserver_databases(res_id):
    """
    Removes a GeoServer network and associated databases.
    """

    logger.info(f"Unregistering GeoServer databases for resource: {res_id}")
    geoserver_namespace = settings.DATA_SERVICES.get("geoserver", {}).get('NAMESPACE')
    geoserver_url = settings.DATA_SERVICES.get("geoserver", {}).get('URL')
    geoserver_user = settings.DATA_SERVICES.get("geoserver", {}).get('USER')
    geoserver_pass = settings.DATA_SERVICES.get("geoserver", {}).get('PASSWORD')
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    params = {
        "update": "overwrite", "recurse": True
    }

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}"

    if geoserver_url is not None:
        response = requests.delete(rest_url, params=params, auth=geoserver_auth, headers=headers)
    else:
        response = None

    logger.info(f"Completed attempt at unregistering GeoServer databases for resource: {res_id}")
    return response


def get_geoserver_data_dir():
    geoserver_directory = settings.DATA_SERVICES.get("geoserver", {}).get('GEOSERVER_DATA_DIR')
    return geoserver_directory


def copy_files_to_geoserver(res_id, db):
    """
    Copy Geospatial file from HydroShare to GeoServer.
    """

    logger.info(f"Copying files to GeoServer for resource: {res_id}")
    geoserver_directory = get_geoserver_data_dir()

    layer_type = None
    layer_name = None
    if db.get("layer_type", None):
        layer_type = db["layer_type"]
    if db.get("layer_name", None):
        layer_name = db["layer_name"]

    error_response = {
        "success": False,
        "type": layer_type,
        "layer_name": layer_name,
        "message": "Error: Unable to copy GeoServer files."
    }

    def get_and_write_file(file_url, file_path):
        try:
            logger.info(f"Getting file from: {file_url}")
            response = requests.get(file_url)
            # create the directory if it doesn't exist
            dir_path = os.path.dirname(file_path) + "/"
            logger.info(f"Checking for directory: {dir_path}")
            os.makedirs(os.path.dirname(dir_path), exist_ok=True)
            with open(file_path, 'w+b') as f:
                logger.info(f"Writing file to GeoServer: {file_path}")
                f.write(response.content)
        except Exception as e:
            message = f"Error getting/writing file: {e}"
            logger.error(message)
            raise Exception(message)

    try:
        hydroshare_url = "/".join(settings.HYDROSHARE_URL.split("/")[:-1])
        file_url = f"{hydroshare_url}/resource/{db['hs_path']}"
        file_path = os.path.join(geoserver_directory, db["hs_path"])
        get_and_write_file(file_url, file_path)
        # Get not only the .shp file but also the .shx, .dbf, and .prj files
        # https://github.com/hydroshare/hydroshare/issues/5631
        logger.info(f"Checking for associated files for resource: {res_id}")
        if db.get("associated_files", None):
            for file in db["associated_files"]:
                logger.info(f"Copying associated file to GeoServer from: {file}")
                file_url = f"{hydroshare_url}/resource/{file}"
                file_path = os.path.join(geoserver_directory, file)
                get_and_write_file(file_url, file_path)
        logger.info(f"Successfully copied files to GeoServer for resource: {res_id}")
        return {
            "success": True,
            "type": layer_type,
            "layer_name": layer_name,
            "message": "Successfully copied GeoServer files."
        }
    except Exception as e:
        message = f"Error copying files to geoserver: {e}"
        error_response["message"] = message
        logger.error(message)
        return error_response


def remove_copied_files_from_geoserver(res_id, db):
    """
    Remove file from GeoServer.
    """

    geoserver_directory = get_geoserver_data_dir()

    layer_type = None
    layer_name = None
    if db.get("layer_type", None):
        layer_type = db["layer_type"]
    if db.get("layer_name", None):
        layer_name = db["layer_name"]

    error_response = {
        "success": False,
        "type": layer_type,
        "layer_name": layer_name,
        "message": "Error: Unable to copy GeoServer files."
    }

    try:
        file_path = os.path.join(geoserver_directory, db["hs_path"])
        logger.info(f"Removing file from GeoServer: {file_path}")
        os.remove(file_path)
        if db.get("associated_files", None):
            for file in db["associated_files"]:
                file_path = os.path.join(geoserver_directory, file)
                logger.info(f"Removing associated file from GeoServer: {file_path}")
                os.remove(file_path)
    except Exception as e:
        message = f"Error removing files from geoserver: {e}"
        error_response["message"] = message
        logger.error(message)
        return error_response
    logger.info("Successfully removed files from GeoServer")
    return {
        "success": True,
        "type": layer_type,
        "layer_name": layer_name,
        "message": "Successfully removed GeoServer files."
    }


def remove_files_for_entire_resource(res_id):
    """
    Remove all files from GeoServer for a resource.
    """

    logger.info(f"Removing all files for entire resource: {res_id}")
    geoserver_directory = get_geoserver_data_dir()

    error_response = {
        "success": False,
        "message": f"Error: Unable to remove GeoServer files for resource {res_id}."
    }

    try:
        dir_path = os.path.join(geoserver_directory, res_id)
        logger.info(f"Removing dir from GeoServer: {dir_path}")
        shutil.rmtree(dir_path)
    except Exception as e:
        message = f"Error removing files from geoserver: {e}"
        error_response["message"] = message
        logger.error(message)
        return error_response
    logger.info("Successfully removed files from GeoServer")
    return {
        "success": True,
        "message": "Successfully removed GeoServer directory."
    }


def register_geoserver_db(res_id, db):
    """
    Attempts to register a GeoServer layer
    """

    logger.info(f"Registering GeoServer layer for resource: {res_id}")
    geoserver_namespace = settings.DATA_SERVICES.get("geoserver", {}).get('NAMESPACE')
    geoserver_url = settings.DATA_SERVICES.get("geoserver", {}).get('URL')
    geoserver_user = settings.DATA_SERVICES.get("geoserver", {}).get('USER')
    geoserver_pass = settings.DATA_SERVICES.get("geoserver", {}).get('PASSWORD')
    geoserver_directory = get_geoserver_data_dir()
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }
    error_message = "Error: Unable to register GeoServer layer."
    error_response = {"success": False, "type": db["layer_type"], "layer_name": db["layer_name"], "message": error_message}

    if any(i in db['layer_name'] for i in [".", ","]):
        logging.error(f"Invalid layer name: {db['layer_name']}")
        return error_response

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{str(db['layer_name']).replace('/', ' ')}/external.{db['file_type']}"
    data = f"file://{geoserver_directory}/{db['hs_path']}"
    response = requests.put(rest_url, data=data, headers=headers, auth=geoserver_auth)

    if response.status_code != 201:
        logging.error(f"Error registering GeoServer layer at {rest_url}: {response}")
        return error_response

    rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{str(db['layer_name']).replace('/', ' ')}/{db['layer_group']}/{db['file_name']}.json"
    response = requests.get(rest_url, headers=headers, auth=geoserver_auth)

    try:
        if json.loads(response.content.decode('utf-8'))[db["verification"]]["enabled"] is False:
            logging.error(f"Verification not enabled for layer: {db['layer_name']}")
            return error_response
    except Exception as e:
        logging.error(f"Error checking verification for layer {db['layer_name']}: {e}")
        return error_response

    bbox = json.loads(response.content)[db["verification"]]["nativeBoundingBox"]

    data = response.content.decode('utf-8').replace('"name":"' + db["file_name"] + '"', '"name":"' + db["layer_name"].replace("/", " ") + '"')
    response = requests.put(rest_url, headers=headers, auth=geoserver_auth, data=data)

    if response.status_code != 200:
        logging.error(f"Error attempting to put layer data at {rest_url}: {response}")
        return error_response

    if db["layer_type"] == "GeographicRaster":
        try:
            hydroshare_url = "/".join(settings.HYDROSHARE_URL.split("/")[:-1])
            layer_vrt_url = f"{hydroshare_url}/resource/{'.'.join(db['hs_path'].split('.')[:-1])}.vrt"
            response = requests.get(layer_vrt_url)
            vrt = etree.fromstring(response.content.decode('utf-8'))
            layer_max = None
            layer_min = None
            layer_ndv = None
            for element in vrt.iterfind(".//MDI"):
                if element.get("key") == "STATISTICS_MAXIMUM":
                    layer_max = element.text
                if element.get("key") == "STATISTICS_MINIMUM":
                    layer_min = element.text

            try:
                layer_ndv = vrt.find(".//NoDataValue").text
            except:
                layer_ndv = None

            if layer_max is not None and layer_min is not None and layer_min < layer_max and layer_ndv is not None:

                layer_style = get_layer_style(layer_max, layer_min, layer_ndv, db["layer_name"].replace("/", " "))

                rest_url = f"{geoserver_url}/workspaces/{workspace_id}/styles"
                headers = {"content-type": "application/vnd.ogc.sld+xml"}
                response = requests.post(rest_url, data=layer_style, auth=geoserver_auth, headers=headers)

                if response.status_code == 201:

                    rest_url = f"{geoserver_url}/layers/{workspace_id}:{db['layer_name'].replace('/', ' ')}"
                    headers = {"content-type": "application/json"}
                    body = '{"layer": {"defaultStyle": {"name": "' + db["layer_name"].replace("/", " ") + '", "href":"https:\/\/geoserver.hydroshare.org\/geoserver\/rest\/styles\/' + db["layer_name"].replace("/", " ") + '.json"}}}'
                    response = requests.put(rest_url, data=body, auth=geoserver_auth, headers=headers)

        except Exception as e:
            pass

    logger.info(f"Successfully registered GeoServer layer: {db}")
    add_string = ""
    if bbox.get("crs", None):
        add_string = f"&srs={bbox['crs']}"
    return {"success": True, "type": db["layer_type"], "layer_name": db["layer_name"], "message": f"{'/'.join((geoserver_url.split('/')[:-1]))}/{workspace_id}/wms?service=WMS&version=1.1.0&request=GetMap&layers={workspace_id}:{urllib.parse.quote(db['layer_name'].replace('/', ' '))}&bbox={bbox['minx']}%2C{bbox['miny']}%2C{bbox['maxx']}%2C{bbox['maxy']}&width=612&height=768&format=application/openlayers{add_string}"}


def unregister_geoserver_db(res_id, db):
    """
    Removes a GeoServer layer
    """

    logger.info(f"Unregistering GeoServer layer: {db}")
    geoserver_namespace = settings.DATA_SERVICES.get("geoserver", {}).get('NAMESPACE')
    geoserver_url = settings.DATA_SERVICES.get("geoserver", {}).get('URL')
    geoserver_user = settings.DATA_SERVICES.get("geoserver", {}).get('USER')
    geoserver_pass = settings.DATA_SERVICES.get("geoserver", {}).get('PASSWORD')
    geoserver_auth = requests.auth.HTTPBasicAuth(
        geoserver_user, 
        geoserver_pass
    )

    workspace_id = f"{geoserver_namespace}-{res_id}"

    headers = {
        "content-type": "application/json"
    }

    params = {
        "update": "overwrite", "recurse": True
    }

    if geoserver_url is not None:
        rest_url = f"{geoserver_url}/workspaces/{workspace_id}/{db['store_type']}/{str(db['layer_name']).replace('/', ' ')}"
        response = requests.delete(rest_url, params=params, headers=headers, auth=geoserver_auth)
    else:
        response = None

    remove_copied_files_from_geoserver(res_id, db)

    logger.info(f"Successfully unregistered GeoServer layer for resource: {res_id}")

    # TODO: ideally we "inform" HS that the registration failed
    # This is called from an async task, so we can't return a meaningful response to HS
    return response


def get_layer_style(max_value, min_value, ndv_value, layer_id):
    """
    Sets default style for raster layers.
    """
    if ndv_value < min_value:
        low_ndv = f'<ColorMapEntry color="#000000" quantity="{ndv_value}" label="nodata" opacity="0.0" />'
        high_ndv = ""
    elif ndv_value > max_value:
        low_ndv = ""
        high_ndv = f'<ColorMapEntry color="#000000" quantity="{ndv_value}" label="nodata" opacity="0.0" />'
    else:
        low_ndv = ""
        high_ndv = ""
    layer_style = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
      xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
      <NamedLayer>
        <Name>simpleraster</Name>
        <UserStyle>
          <Name>{layer_id}</Name>
          <Title>Default raster style</Title>
          <Abstract>Default greyscale raster style</Abstract>
          <FeatureTypeStyle>
            <Rule>
              <RasterSymbolizer>
                <Opacity>1.0</Opacity>
                <ColorMap>
                  {low_ndv}
                  <ColorMapEntry color="#000000" quantity="{min_value}" label="values" />
                  <ColorMapEntry color="#FFFFFF" quantity="{max_value}" label="values" />
                  {high_ndv}
                </ColorMap>
              </RasterSymbolizer>
            </Rule>
          </FeatureTypeStyle>
        </UserStyle>
      </NamedLayer>
    </StyledLayerDescriptor>"""

    return layer_style


def get_list_of_public_geo_resources():
    logger.info("Getting list of public geospatial resources")
    hydroshare_url = "/".join(settings.HYDROSHARE_URL.split("/")[:-1])
    types = ["Geographic Feature (ESRI Shapefiles)", "Geographic Raster"]
    # replace spaces with + for the query string
    types = [t.replace(" ", "+") for t in types]
    params = {
        "type": types,
        "availability": ["public", "published"],
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
    for i in range(1, page_count + 1):
        print(f"Getting page {i}")
        response = requests.get(f"{rest_url}&pnum={i}")
        response_json = response.json()
        resources = json.loads(response_json.get('resources', []))
        new_ids = [resource["short_id"] for resource in resources if resource.get('short_id', None)]
        res_ids.extend(new_ids)
    print(f"Found {len(res_ids)} public geospatial resources")
    print(f"Should match {rescount}")
    return res_ids