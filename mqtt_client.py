# mqtt_client.py: Manejo de conexión MQTT

import json
import time
import threading
import queue
from paho.mqtt import client as mqtt
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
import config

# Queues para pasar datos a otros módulos (thread-safe)
temperature_queue = queue.Queue()  # Para nuevos datos de temperatura
heartbeat_status_queue = queue.Queue()  # Para status: "online" o "offline"

class MQTTClient(QObject):
    # Signals para alertas (usaremos en GUI más adelante)
    alert_signal = pyqtSignal(str)  # Para emitir alertas como "offline"

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.last_heartbeat = 0  # Timestamp del último heartbeat
        self.last_temperature_data = None  # Último dato de temperatura recibido
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.check_heartbeat)
        self.heartbeat_timer.start(5000)  # Chequea cada 5 seg

    def connect(self):
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        self.client.loop_start()  # Inicia loop en background

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Conectado al broker MQTT")
            client.subscribe(config.MQTT_TOPIC_TEMPERATURE)
            client.subscribe(config.MQTT_TOPIC_HEARTBEAT)
        else:
            print(f"Error de conexión: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == config.MQTT_TOPIC_TEMPERATURE:
                self.handle_temperature(payload)
            elif msg.topic == config.MQTT_TOPIC_HEARTBEAT:
                self.handle_heartbeat(payload)
        except json.JSONDecodeError:
            print("Error parsing JSON")

    def handle_temperature(self, data):
        # Extrae datos relevantes
        self.last_temperature_data = {
            'device_id': data.get('device_id'),
            'timestamp': data.get('timestamp'),
            'temperature': data.get('temperature'),
            'pressure': data.get('pressure'),
            'altitude': data.get('altitude'),
            'rssi': data.get('rssi'),
            'status': data.get('status')
        }
        # Pasa a queue para GUI/DB
        temperature_queue.put(self.last_temperature_data)
        print(f"Nuevo dato de temperatura: {self.last_temperature_data['temperature']}°C")

    def handle_heartbeat(self, data):
        if data.get('status') == 'alive':
            self.last_heartbeat = time.time()  # Actualiza timestamp
            heartbeat_status_queue.put("online")
            print("Heartbeat recibido: Dispositivo alive")

    def check_heartbeat(self):
        if time.time() - self.last_heartbeat > config.HEARTBEAT_TIMEOUT:
            heartbeat_status_queue.put("offline")
            self.alert_signal.emit("Dispositivo offline: No se recibe heartbeat")
            print("Alerta: Dispositivo offline")

def run_mqtt():
    mqtt_client = MQTTClient()
    mqtt_client.connect()
    # Mantiene el thread vivo
    while True:
        time.sleep(1)