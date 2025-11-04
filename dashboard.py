# dashboard.py: Clase principal de la GUI

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget, 
                              QMessageBox, QMainWindow, QDateEdit, QPushButton, 
                              QHBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import QTimer, QDate
from PyQt6.QtGui import QFont
import queue
import datetime
import db_handler
import mqtt_client
import widgets

class Dashboard(QMainWindow):
    def __init__(self, mqtt_client_instance, anomaly_detector, db_instance):
        super().__init__()
        self.mqtt_client = mqtt_client_instance
        self.anomaly_detector = anomaly_detector
        self.db = db_instance
        
        self.setWindowTitle("Refrigerator Monitor Dashboard")
        self.setGeometry(100, 100, 1000, 700)
        
        # Tabs principales
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # === PESTAÑA 1: Dashboard en tiempo real ===
        self.dashboard_tab = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_tab)
        
        # Labels de información
        font_bold = QFont()
        font_bold.setPointSize(11)
        font_bold.setBold(True)
        
        self.temp_label = QLabel("🌡️ Temperatura actual: Esperando datos...")
        self.temp_label.setFont(font_bold)
        
        self.rssi_label = QLabel("📶 RSSI: N/A")
        self.status_label = QLabel("🔌 Status: Inicializando...")
        self.alert_label = QLabel("⚠️ Alertas: Ninguna")
        self.alert_label.setStyleSheet("color: green; font-weight: bold; font-size: 12pt;")
        self.save_label = QLabel("💾 Último guardado en DB: N/A")
        
        # Gráfico de temperatura
        self.plot = widgets.TemperaturePlot()
        
        # Agrega widgets al layout
        self.dashboard_layout.addWidget(self.temp_label)
        self.dashboard_layout.addWidget(self.rssi_label)
        self.dashboard_layout.addWidget(self.status_label)
        self.dashboard_layout.addWidget(self.alert_label)
        self.dashboard_layout.addWidget(self.save_label)
        self.dashboard_layout.addWidget(self.plot)
        
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # === PESTAÑA 2: Datos históricos ===
        self.historical_tab = QWidget()
        self.historical_layout = QVBoxLayout(self.historical_tab)
        
        # Filtros de fecha
        filter_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        load_button = QPushButton("🔍 Cargar Datos")
        load_button.clicked.connect(self.load_historical_data)
        
        filter_layout.addWidget(QLabel("Desde:"))
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("Hasta:"))
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addWidget(load_button)
        filter_layout.addStretch()
        
        self.historical_layout.addLayout(filter_layout)
        
        # Tabla de datos
        self.historical_table = QTableWidget()
        self.historical_table.setColumnCount(4)
        self.historical_table.setHorizontalHeaderLabels([
            "ID", "Device ID", "Fecha/Hora", "Temperatura (°C)"
        ])
        self.historical_table.setColumnWidth(0, 50)
        self.historical_table.setColumnWidth(1, 150)
        self.historical_table.setColumnWidth(2, 200)
        self.historical_table.setColumnWidth(3, 150)
        
        self.historical_layout.addWidget(self.historical_table)
        
        self.tabs.addTab(self.historical_tab, "📋 Datos Históricos")
        
        # === Timer para actualizar UI ===
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(500)  # Actualiza cada 500ms
        
        # === Conecta signals para alertas ===
        self.mqtt_client.alert_signal.connect(self.show_alert)
        self.anomaly_detector.alert_signal.connect(self.show_anomaly_alert)
        
        self.current_status = "offline"
        self.last_alert_message = ""

    def load_historical_data(self):
        """Carga datos históricos desde la DB"""
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        data = self.db.get_historical_data(start_date=start_date, end_date=end_date)
        
        self.historical_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.historical_table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.historical_table.setItem(row, 1, QTableWidgetItem(item['device_id']))
            self.historical_table.setItem(row, 2, QTableWidgetItem(str(item['timestamp'])))
            self.historical_table.setItem(row, 3, QTableWidgetItem(f"{item['temperature']:.2f}"))
        
        print(f"✓ Cargados {len(data)} registros históricos")

    def update_ui(self):
        """Actualiza la interfaz con nuevos datos"""
        # Actualiza temperatura desde la queue
        try:
            data = mqtt_client.temperature_queue.get_nowait()
            temp = data['temperature']
            rssi = data['rssi']
            status = data['status']
            
            self.temp_label.setText(f"🌡️ Temperatura actual: {temp}°C")
            self.rssi_label.setText(f"📶 RSSI: {rssi} dBm")
            
            # Actualiza gráfico
            self.plot.update_plot(temp)
        except queue.Empty:
            pass
        
        # Actualiza status de heartbeat
        try:
            hb_status = mqtt_client.heartbeat_status_queue.get_nowait()
            self.current_status = hb_status
            
            if hb_status == "online":
                self.status_label.setText("🔌 Status: ✅ Online")
                self.status_label.setStyleSheet("color: green;")
                # Limpia alerta de offline si había
                if "offline" in self.last_alert_message.lower():
                    self.alert_label.setText("⚠️ Alertas: Ninguna")
                    self.alert_label.setStyleSheet("color: green; font-weight: bold; font-size: 12pt;")
            else:
                self.status_label.setText("🔌 Status: ❌ Offline")
                self.status_label.setStyleSheet("color: red;")
        except queue.Empty:
            pass

        # Chequea notificaciones de guardado en DB
        try:
            save_ts = db_handler.save_queue.get_nowait()
            self.save_label.setText(f"💾 Último guardado en DB: {save_ts}")
        except queue.Empty:
            pass

    def show_alert(self, message):
        """Muestra alerta de dispositivo offline"""
        self.last_alert_message = message
        self.alert_label.setText(f"⚠️ Alertas: {message}")
        self.alert_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        QMessageBox.warning(self, "⚠️ Alerta", message)

    def show_anomaly_alert(self, message):
        """Muestra alerta de anomalía en temperatura"""
        self.last_alert_message = message
        self.alert_label.setText(f"⚠️ Alertas: {message}")
        
        if "crítica" in message.lower():
            self.alert_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        else:
            self.alert_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12pt;")
        
        # Solo muestra popup para alertas críticas
        if "crítica" in message.lower():
            QMessageBox.critical(self, "🚨 Alerta Crítica", message)