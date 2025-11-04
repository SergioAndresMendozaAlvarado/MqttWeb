# widgets.py: Widgets personalizados para la GUI

from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class TemperaturePlot(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Temperatura (°C)')
        self.plot_widget.setLabel('bottom', 'Tiempo (segundos)')
        self.plot_widget.showGrid(x=True, y=True)
        
        self.curve = self.plot_widget.plot(pen='b')  # Línea azul para temperatura
        self.data_x = []  # Tiempos relativos
        self.data_y = []  # Temperaturas
        self.max_points = 100  # Limita a últimos 100 puntos

    def update_plot(self, new_temp):
        current_time = len(self.data_x) * 15  # Asume 15 seg por punto
        self.data_x.append(current_time)
        self.data_y.append(new_temp)
        
        if len(self.data_x) > self.max_points:
            self.data_x = self.data_x[-self.max_points:]
            self.data_y = self.data_y[-self.max_points:]
        
        self.curve.setData(self.data_x, self.data_y)