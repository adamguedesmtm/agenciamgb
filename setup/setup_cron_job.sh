#!/bin/bash

# Add cron job for backup
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -

echo "Cron job for backup added."