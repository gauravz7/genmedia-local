#!/bin/bash

# Get the absolute path to the current directory
APP_PATH=$(cd "$(dirname "$0")" && pwd)

# Define service and file paths
SERVICE_NAME="com.google.app"
PLIST_PATH="$HOME/Library/LaunchAgents/$SERVICE_NAME.plist"
LOG_FILE="$APP_PATH/app.log"
ERROR_LOG_FILE="$APP_PATH/app.error.log"
PYTHON_PATH=$(which python)

echo "Stopping and removing any existing service..."
launchctl unload "$PLIST_PATH" 2>/dev/null
rm "$PLIST_PATH" 2>/dev/null
sleep 1

echo "Creating new launchd service file at $PLIST_PATH..."

# Create the .plist file with dynamic paths
cat > "$PLIST_PATH" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$APP_PATH/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$ERROR_LOG_FILE</string>
    <key>WorkingDirectory</key>
    <string>$APP_PATH</string>
</dict>
</plist>
EOL

echo "Loading and starting the application service..."

# Load the service
launchctl load "$PLIST_PATH"
if [ $? -ne 0 ]; then
    echo "Failed to load the service. Please check the plist file at $PLIST_PATH"
    exit 1
fi

# Start the service
launchctl start "$SERVICE_NAME"
if [ $? -ne 0 ]; then
    echo "Failed to start the service."
    exit 1
fi

echo ""
echo "Application service has been started successfully."
echo "It is now running in the background."
echo ""
echo "You can access it at: http://localhost:8080"
echo ""
echo "To view live logs, run the following command in a new terminal:"
echo "tail -f $LOG_FILE"
echo ""
echo "To view error logs, run:"
echo "tail -f $ERROR_LOG_FILE"
echo ""
echo "To stop the service, run:"
echo "launchctl unload $PLIST_PATH && rm $PLIST_PATH"
