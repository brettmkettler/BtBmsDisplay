# Create the systemd service file
sudo tee /etc/systemd/system/j5-ui.service > /dev/null << 'EOF'
[Unit]
Description=J5 Console UI Service
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/Users/brettkettler/REPO/j5_console/BtBmsDisplay
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/bin/bash -c "cd /Users/brettkettler/REPO/j5_console/BtBmsDisplay && /usr/bin/npm run start & sleep 5 && ./start_kiosk.sh"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF