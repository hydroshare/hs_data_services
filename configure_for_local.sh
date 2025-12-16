#!/bin/bash

# HydroShare Configuration Script - COMPLETE WORKING VERSION
# This script automates the setup of HydroShare local settings

set -e  # Exit on error

echo "================================================"
echo "HydroShare Configuration Script"
echo "================================================"

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ $1 failed"
        return 1
    fi
}

# Step 1: Create Django Authentication Token
echo ""
echo "Step 1: Creating Django Authentication Token"
echo "--------------------------------------------"

CONTAINER_NAME="hs_data_services-celery-worker-1"
echo "Using container: $CONTAINER_NAME"

# Try the direct approach that mimics manual entry
echo "Attempting to create token..."
API_TOKEN=$(docker exec -it "$CONTAINER_NAME" /bin/bash -c "
cd /home/dsuser/hs_data_services
python manage.py shell << 'PYTHONEOF'
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
Token.objects.filter(user=admin).delete()
token = Token.objects.create(user=admin)
print('TOKEN_RESULT:' + token.key)
PYTHONEOF
" 2>&1 | grep "TOKEN_RESULT:" | cut -d':' -f2- | tr -d '[:space:]')

if [ ! -z "$API_TOKEN" ] && [[ "$API_TOKEN" =~ ^[a-f0-9]{40}$ ]]; then
    echo "✓ Authentication token created: $API_TOKEN"
else
    echo "Automatic token creation failed."
    echo ""
    echo "========================================================"
    echo "MANUAL TOKEN CREATION REQUIRED"
    echo "========================================================"
    echo ""
    echo "Please run these commands MANUALLY:"
    echo ""
    echo "1. First, enter the container:"
    echo "   docker exec -it $CONTAINER_NAME /bin/bash"
    echo ""
    echo "2. Then run these exact commands:"
    echo "   cd /home/dsuser/hs_data_services"
    echo "   python manage.py shell"
    echo ""
    echo "3. In the Python shell, paste ALL these lines at once:"
    echo "from rest_framework.authtoken.models import Token"
    echo "from django.contrib.auth import get_user_model"
    echo "User = get_user_model()"
    echo "admin = User.objects.get(username='admin')"
    echo "Token.objects.filter(user=admin).delete()"
    echo "token = Token.objects.create(user=admin)"
    echo "print('TOKEN:' + token.key)"
    echo ""
    echo "4. Copy ONLY the token (the 40-character string)"
    echo "5. Exit Python: exit()"
    echo "6. Exit container: exit"
    echo ""
    echo "========================================================"
    read -p "Paste the token here: " API_TOKEN
    
    if [ -z "$API_TOKEN" ]; then
        echo "No token provided. Exiting."
        exit 1
    fi
fi

echo ""
echo "✓ Token obtained successfully!"

# Step 2: Update local_settings.py
echo ""
echo "Step 2: Updating local_settings.py"
echo "----------------------------------"

# Ask for settings file location
DEFAULT_SETTINGS="../hydroshare/hydroshare/local_settings.py"
read -p "Enter the path to hydroshare local_settings.py file [default: $DEFAULT_SETTINGS]: " SETTINGS_FILE
SETTINGS_FILE=${SETTINGS_FILE:-$DEFAULT_SETTINGS}

if [ ! -f "${SETTINGS_FILE}" ]; then
    echo "File not found: $SETTINGS_FILE"
    
    # Try to find it
    echo "Searching for local_settings.py..."
    FOUND_SETTINGS=$(find /hydroshare /opt/hydroshare /home -name "local_settings.py" -type f 2>/dev/null | head -5)
    
    if [ ! -z "$FOUND_SETTINGS" ]; then
        echo "Found potential settings files:"
        echo "$FOUND_SETTINGS"
        echo ""
        read -p "Enter the correct path from above or provide a new path: " SETTINGS_FILE
    fi
    
    if [ ! -f "${SETTINGS_FILE}" ]; then
        read -p "File still not found. Would you like to create it? (y/n): " CREATE_FILE
        if [[ $CREATE_FILE =~ ^[Yy]$ ]]; then
            # Create directory if needed
            mkdir -p "$(dirname "$SETTINGS_FILE")"
            touch "$SETTINGS_FILE"
            check_status "Created settings file: $SETTINGS_FILE"
        else
            echo "Please provide an existing file path."
            exit 1
        fi
    fi
fi

# Backup the original file
BACKUP_FILE="${SETTINGS_FILE}.backup.$(date +%Y%m%d%H%M%S)"
cp "$SETTINGS_FILE" "$BACKUP_FILE"
check_status "Backup created: $BACKUP_FILE"

# Add or update settings
echo "Updating settings in $SETTINGS_FILE..."

# Create a temporary file
TEMP_FILE=$(mktemp)

# Copy existing settings, removing our target lines
grep -v -E "^(HSWS_URL|HSWS_API_TOKEN|HSWS_TIMEOUT|HSWS_ACTIVATED)" "$SETTINGS_FILE" > "$TEMP_FILE" 2>/dev/null || cat "$SETTINGS_FILE" > "$TEMP_FILE"

# Append new settings
cat >> "$TEMP_FILE" << EOF

# HydroShare Web Services Configuration
HSWS_URL = 'http://host.docker.internal/his/services/update'
HSWS_GEOSERVER_URL = 'http://host.docker.internal/geoserver'
HSWS_PUBLISH_URLS = False
HSWS_API_TOKEN = '$API_TOKEN'
HSWS_TIMEOUT = 10
HSWS_ACTIVATED = True
HSWS_GEOSERVER_ESCAPE = {
    '/': ' '
}
EOF

# Replace the original file
mv "$TEMP_FILE" "$SETTINGS_FILE"

check_status "Settings updated"

# Step 3: GeoServer Configuration
echo ""
echo "Step 3: Configuring GeoServer"
echo "----------------------------"

echo "Please configure GeoServer:"
echo "1. Go to http://host.docker.internal/geoserver/web"
echo "2. Log in with username: admin, password: geoserver"
echo "3. Go to Global Settings: http://host.docker.internal/geoserver/web/wicket/bookmarkable/org.geoserver.web.admin.GlobalSettingsPage?4&filter=false"
echo "4. Change 'Proxy Base URL' to: http://host.docker.internal/geoserver"
echo "5. Click 'Save'"
echo ""
echo "Note: This is necessary for proper navigation in the GeoServer web interface."
read -p "Press Enter after completing GeoServer configuration..."

echo ""
echo "================================================"
echo "Configuration Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "1. Django authentication token created: $API_TOKEN"
echo "2. Settings updated in: $SETTINGS_FILE"
echo "3. Backup created at: $BACKUP_FILE"
echo "4. GeoServer configuration completed manually"
echo ""
echo "Important next steps:"
echo "1. Restart HydroShare services if needed."
echo ""
echo "2. Test the full setup:"
echo "   - HIS Django admin: http://host.docker.internal/his/admin"
echo "   - GeoServer: http://host.docker.internal/geoserver/web"
echo "   - HydroShare at: http://localhost:8000"
echo ""
echo "3. If you need to recreate the token later:"
echo "   docker exec -it $CONTAINER_NAME /bin/bash"
echo "   cd /home/dsuser/hs_data_services"
echo "   python manage.py shell"
echo "   Then run:"
echo "   from rest_framework.authtoken.models import Token"
echo "   from django.contrib.auth import get_user_model"
echo "   User = get_user_model()"
echo "   admin = User.objects.get(username='admin')"
echo "   Token.objects.filter(user=admin).delete()"
echo "   token = Token.objects.create(user=admin)"
echo "   print(token.key)"
echo ""
echo "================================================"