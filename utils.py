# utils.py: Funciones auxiliares

import json
from datetime import datetime
import logging

# Configura logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_mqtt_payload(payload):
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logging.error("Error parsing JSON")
        return None

def is_hourly_save_time(now=None):
    if now is None:
        now = datetime.now()
    return now.minute == 0 and now.second < 15

def format_timestamp(ts):
    return str(ts)