# config.py: Configuraciones globales para el proyecto

# MQTT Broker (Mosquitto)
MQTT_BROKER = "192.168.0.2"  # Cambia a tu host real
MQTT_PORT = 1883
MQTT_USERNAME = None  # Si requiere auth, agrega usuario
MQTT_PASSWORD = None  # Si requiere auth, agrega password
MQTT_TOPIC_TEMPERATURE = "fridge/esp32-fridge-001/sensor_data"
MQTT_TOPIC_HEARTBEAT = "fridge/esp32-fridge-001/heartbeat"

# Base de Datos MariaDB/MySQL
DB_HOST = "localhost"  # O "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "7843"  #
DB_NAME = "refrigerator_db"

# Heartbeat
HEARTBEAT_INTERVAL = 5
HEARTBEAT_TIMEOUT = 10

# Guardado en DB
SAVE_INTERVAL = "hourly"

# Detección de anomalías
ANOMALY_WINDOW_SIZE = 20  # ~5 min con datos cada 15 seg
ANOMALY_Z_THRESHOLD = 2.5  # Umbral de Z-score
ANOMALY_DURATION_THRESHOLD = 120  # 2 min para considerar anomalía sostenida vs temporal