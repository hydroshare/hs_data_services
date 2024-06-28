#!/bin/bash

# Add tomcat user and edit permissions
addgroup --gid 1099 tomcat && useradd -m -u 1099 -g tomcat tomcat \
    && chown -R tomcat:tomcat . \
    && chown -R tomcat:tomcat "/var/local/geoserver" \
    && chown -R tomcat:tomcat "/usr/local/geoserver" \
    && chown -R tomcat:tomcat "/var/local/geoserver-exts"

# Add custom user ID
if [ -n "${CUSTOM_UID}" ];then
  echo "Using custom UID ${CUSTOM_UID}."
  usermod -u ${CUSTOM_UID} tomcat
  find / -path /geoserver_resources -prune -false -o -user 1099 -exec chown -h tomcat {} \; 
fi

# Add custom group ID
if [ -n "${CUSTOM_GID}" ];then
  echo "Using custom GID ${CUSTOM_GID}."
  groupmod -g ${CUSTOM_GID} tomcat
  find / -path /geoserver_resources -prune -false -o -group 1099 -exec chgrp -h tomcat {} \;
fi

# Allow Anonymous GET Access
sed -i 's/GET=ADMIN/GET=IS_AUTHENTICATED_ANONYMOUSLY/g' /var/local/geoserver/security/rest.properties

for ext in `ls -d "${GEOSERVER_EXT_DIR}"/*/`; do
  su tomcat -c "cp "${ext}"*.jar /usr/local/geoserver/WEB-INF/lib"
done

# Run GeoServer
su tomcat -c "/usr/local/tomcat/bin/catalina.sh run"
