# db_handler.py: Lógica de base de datos MySQL

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import queue
import config

# Queue global para notificar a la GUI cuando se guarda en DB
save_queue = queue.Queue()

class DBHandler:
    def __init__(self):
        self.connection = None
        self.last_saved_hour = None
        self.connect()
        self.create_database_and_table()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            print("✓ Conectado a MySQL")
        except Error as e:
            if "Unknown database" in str(e):
                # Si DB no existe, conecta sin DB para crearla
                self.connection = mysql.connector.connect(
                    host=config.DB_HOST,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD
                )
                print("⚠ DB no existe, se creará automáticamente")
            else:
                print(f"✗ Error conectando a MySQL: {e}")
                raise

    def create_database_and_table(self):
        cursor = self.connection.cursor()
        try:
            # Crea DB si no existe
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
            cursor.execute(f"USE {config.DB_NAME}")
            
            # Crea tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hourly_temperatures (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(50) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    temperature FLOAT NOT NULL,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_device (device_id)
                )
            """)
            self.connection.commit()
            print("✓ DB y tabla verificadas/creadas")
        except Error as e:
            print(f"✗ Error creando DB/tabla: {e}")
        finally:
            cursor.close()

    def insert_temperature(self, device_id, temperature):
        now = datetime.now()
        hour_timestamp = now.replace(minute=0, second=0, microsecond=0)
        
        # Evita duplicados en la misma hora
        if self.last_saved_hour == hour_timestamp:
            print("⚠ Ya guardado en esta hora, omitiendo...")
            return
        
        cursor = self.connection.cursor()
        try:
            query = """
                INSERT INTO hourly_temperatures (device_id, timestamp, temperature)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (device_id, hour_timestamp, temperature))
            self.connection.commit()
            self.last_saved_hour = hour_timestamp
            print(f"✓ Guardado en DB: {temperature}°C a las {hour_timestamp.strftime('%H:%M')}")
            return True
        except Error as e:
            print(f"✗ Error insertando en DB: {e}")
            return False
        finally:
            cursor.close()

    def get_historical_data(self, start_date=None, end_date=None):
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM hourly_temperatures"
        params = []
        
        if start_date:
            query += " WHERE timestamp >= %s"
            params.append(start_date.strftime('%Y-%m-%d 00:00:00'))
        
        if end_date:
            clause = " AND" if "WHERE" in query else " WHERE"
            query += f"{clause} timestamp < %s"
            params.append(end_date.strftime('%Y-%m-%d 23:59:59'))
        
        query += " ORDER BY timestamp DESC"
        
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"✗ Error obteniendo datos históricos: {e}")
            return []
        finally:
            cursor.close()