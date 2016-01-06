#!/bin/bash

process_name="entry_monitor_main.py"
process_id=$(ps aux | grep "$process_name" | grep -v "grep" | head -1 | awk '{print $2}')
kill -9 $process_id
