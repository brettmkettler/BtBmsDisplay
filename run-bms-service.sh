#!/bin/bash

# Wrapper script to run BMS service with full user session context
# This simulates running the script manually in a terminal

exec su - seanfuchs -c "
cd /home/seanfuchs/Desktop/j5_console/BtBmsDisplay && 
source /home/seanfuchs/Desktop/venv/bin/activate && 
python dual_bms_service.py
"
