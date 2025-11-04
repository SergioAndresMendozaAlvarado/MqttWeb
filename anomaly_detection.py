# anomaly_detection.py: Detección de anomalías en temperatura

import collections
import time
import numpy as np
from sklearn.ensemble import IsolationForest
from PyQt6.QtCore import pyqtSignal, QObject
import config

class AnomalyDetector(QObject):
    alert_signal = pyqtSignal(str)  # Signal para alertas a GUI

    def __init__(self):
        super().__init__()
        self.window = collections.deque(maxlen=config.ANOMALY_WINDOW_SIZE)
        self.timestamps = collections.deque(maxlen=config.ANOMALY_WINDOW_SIZE)
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.last_train_time = 0
        self.anomaly_start_time = 0
        self.is_anomaly_active = False
        self.grace_period_active = False
        self.last_normal_time = time.time()

    def process_data(self, temperature, timestamp):
        """Procesa nueva lectura de temperatura y detecta anomalías"""
        self.window.append(temperature)
        self.timestamps.append(timestamp)
        
        # Necesita ventana completa para análisis
        if len(self.window) < config.ANOMALY_WINDOW_SIZE:
            print(f"📊 Recopilando datos iniciales: {len(self.window)}/{config.ANOMALY_WINDOW_SIZE}")
            return
        
        # === MÉTODO 1: Análisis estadístico (EWMA + Z-score) ===
        data = np.array(self.window)
        ewma = self.exponential_moving_average(data)
        std = np.std(data)
        
        if std == 0:
            std = 0.1  # Evita división por cero
        
        z_score = (temperature - ewma) / std
        is_stat_anomaly = abs(z_score) > config.ANOMALY_Z_THRESHOLD
        
        # === MÉTODO 2: Machine Learning (Isolation Forest) ===
        # Re-entrena cada 60 segundos
        if time.time() - self.last_train_time > 60:
            self.model.fit(data.reshape(-1, 1))
            self.last_train_time = time.time()
            print("🤖 Modelo ML reentrenado")
        
        ml_score = self.model.decision_function([[temperature]])[0]
        is_ml_anomaly = ml_score < -0.5
        
        # === DETECCIÓN: Ambos métodos deben coincidir ===
        is_anomaly = is_stat_anomaly and is_ml_anomaly
        
        if is_anomaly:
            if not self.is_anomaly_active:
                self.anomaly_start_time = time.time()
                self.is_anomaly_active = True
                print(f"🔔 Anomalía detectada: {temperature}°C (Z-score: {z_score:.2f}, ML: {ml_score:.2f})")
            
            duration = time.time() - self.anomaly_start_time
            
            # Anomalía temporal (posible apertura de puerta)
            if duration < config.ANOMALY_DURATION_THRESHOLD:
                if not self.grace_period_active:
                    alert_msg = f"⚠️ Cambio temporal: {temperature}°C (posible apertura)"
                    self.alert_signal.emit(alert_msg)
                    print(alert_msg)
                    self.grace_period_active = True
            else:
                # Anomalía sostenida (problema crítico)
                alert_msg = f"🚨 ALERTA CRÍTICA: Cambio sostenido ({duration:.0f}s) - {temperature}°C"
                self.alert_signal.emit(alert_msg)
                print(alert_msg)
        else:
            # Temperatura normal
            if self.is_anomaly_active:
                recovery_time = time.time() - self.anomaly_start_time
                print(f"✅ Temperatura normalizada después de {recovery_time:.0f}s")
                self.is_anomaly_active = False
                self.grace_period_active = False
            
            self.last_normal_time = time.time()

    def exponential_moving_average(self, data, alpha=0.3):
        """Calcula promedio móvil exponencial"""
        ema = data[0]
        for val in data[1:]:
            ema = alpha * val + (1 - alpha) * ema
        return ema