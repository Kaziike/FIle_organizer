#!/bin/bash

# Auto-installer script for File Organizer Systemd User Service

SERVICE_NAME="file-organizer.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SCRIPT_PATH="$(readlink -f "$(dirname "$0")/file_organizer.py")"

if [ "$1" == "--uninstall" ] || [ "$1" == "uninstall" ]; then
    echo "Uninstalling $SERVICE_NAME..."
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null
    rm -f "$SYSTEMD_USER_DIR/$SERVICE_NAME"
    systemctl --user daemon-reload
    echo "Successfully uninstalled File Organizer service."
    exit 0
fi

echo "============================================="
echo " Installing File Organizer Systemd Service   "
echo "============================================="

# Ensure systemd user directory exists
mkdir -p "$SYSTEMD_USER_DIR"

# Generate systemd unit file
SERVICE_FILE="$SYSTEMD_USER_DIR/$SERVICE_NAME"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Automated File Organizer Service for ~/Downloads
After=network.target

[Service]
Type=simple
WorkingDirectory=$(dirname "$SCRIPT_PATH")
ExecStart=/usr/bin/python3 $SCRIPT_PATH --watch --interval 5
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

echo "1. Service unit created at: $SERVICE_FILE"

# Reload systemd user daemon
systemctl --user daemon-reload
echo "2. Systemd user daemon reloaded."

# Enable and start service
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"
echo "3. Service enabled and started."

echo "---------------------------------------------"
echo "Status of $SERVICE_NAME:"
systemctl --user status "$SERVICE_NAME" --no-pager
echo "============================================="
echo "Installation complete!"
echo "To view live logs, run: journalctl --user -u file-organizer -f"
echo "To uninstall, run: ./install.sh --uninstall"

