#!/bin/bash

# Wrapper script to run BMS service with proper environment
# This matches the environment when running manually

cd /home/seanfuchs/Desktop/j5_console/BtBmsDisplay

# Activate virtual environment
source /home/seanfuchs/Desktop/venv/bin/activate

# Run the service
exec python dual_bms_service.py
