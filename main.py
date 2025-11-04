# main.py: Punto de entrada principal de la aplicación

import sys
import traceback

def main():
    try:
        print("Iniciando aplicación...")
        print("1. Importando módulos...")
        
        import threading
        import time
        from PyQt6.QtWidgets import QApplication
        print("   ✓ PyQt6")
        
        import config
        print("   ✓ config")
        
        import mqtt_client
        print("   ✓ mqtt_client")
        
        import db_handler
        print("   ✓ db_handler")
        
        import anomaly_detection
        print("   ✓ anomaly_detection")
        
        import dashboard
        print("   ✓ dashboard")
        
        print("\n2. Creando aplicación Qt...")
        app = QApplication(sys.argv)
        print("   ✓ QApplication creada")

        print("\n3. Creando instancias...")
        print("   - Creando MQTT Client...")
        mqtt_instance = mqtt_client.MQTTClient()
        print("   ✓ MQTT Client")
        
        print("   - Creando Anomaly Detector...")
        anomaly_instance = anomaly_detection.AnomalyDetector()
        print("   ✓ Anomaly Detector")
        
        print("   - Creando DB Handler...")
        db_instance = db_handler.DBHandler()
        print("   ✓ DB Handler")

        print("\n4. Iniciando threads...")
        
        # Thread MQTT
        def run_mqtt_thread():
            mqtt_instance.connect()
            while True:
                time.sleep(1)
        
        mqtt_thread = threading.Thread(target=run_mqtt_thread, daemon=True)
        mqtt_thread.start()
        print("   ✓ Cliente MQTT iniciado")

        # Thread DB saver
        def run_db_saver_thread():
            last_data = None
            last_data_timestamp = time.time()
            
            while True:
                now = time.time()
                current_minute = time.localtime(now).tm_min
                
                if current_minute == 0 and last_data:
                    if (now - last_data_timestamp) < 30:
                        db_instance.insert_temperature(
                            last_data['device_id'], 
                            last_data['temperature']
                        )
                        db_handler.save_queue.put(time.strftime('%Y-%m-%d %H:%M:%S'))
                        time.sleep(60)
                
                try:
                    new_data = mqtt_client.temperature_queue.get(timeout=0.1)
                    last_data = new_data
                    last_data_timestamp = time.time()
                except:
                    pass
                
                time.sleep(1)
        
        db_thread = threading.Thread(target=run_db_saver_thread, daemon=True)
        db_thread.start()
        print("   ✓ DB saver iniciado")

        # Thread Anomaly detector
        def run_anomaly_thread():
            while True:
                try:
                    data = mqtt_client.temperature_queue.get(timeout=1)
                    temp = data['temperature']
                    ts = time.time()
                    anomaly_instance.process_data(temp, ts)
                    mqtt_client.temperature_queue.put(data)
                except:
                    pass
                time.sleep(0.1)
        
        anomaly_thread = threading.Thread(target=run_anomaly_thread, daemon=True)
        anomaly_thread.start()
        print("   ✓ Anomaly detector iniciado")

        print("\n5. Creando GUI...")
        main_window = dashboard.Dashboard(mqtt_instance, anomaly_instance, db_instance)
        print("   ✓ Dashboard creado")
        
        main_window.show()
        print("   ✓ GUI visible")
        
        print("\n" + "="*60)
        print("✅ DASHBOARD EJECUTÁNDOSE")
        print("="*60 + "\n")

        sys.exit(app.exec())
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR CRÍTICO:")
        print("="*60)
        print(f"\nTipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("\nTraceback completo:")
        traceback.print_exc()
        print("\n" + "="*60)
        input("\nPresiona ENTER para cerrar...")
        sys.exit(1)

if __name__ == "__main__":
    main()