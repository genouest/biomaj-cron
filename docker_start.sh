#!/bin/bash
biomaj_load_cron.py
gunicorn -b 0.0.0.0:5000 -D --capture-output --error-logfile /var/log/biomaj-web.log biomaj_cron.biomaj_cron_web:app
cron -f && tail -f /var/log/cron.log
