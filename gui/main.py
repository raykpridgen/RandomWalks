import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QSlider, QLabel, QHBoxLayout
)
from PyQt6.QtCore import QTimer, Qt
import pyqtgraph as pg


class ParticleSimulation(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Discrete Particle Simulation")
        self.setGeometry(100, 100, 900, 600)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # PyQtGraph Scatter Plot
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        # Sliders for controlling movement parameters
        self.sliders = {}
        self.slider_labels = {}
        self.slider_values = {
            "Step Size": 5,  # Controls movement per step
            "Particle Count": 50  # Number of particles
        }

        for param in self.slider_values:
            h_layout = QHBoxLayout()
            label = QLabel(f"{param}: {self.slider_values[param]}")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(100)
            slider.setValue(self.slider_values[param])
            slider.valueChanged.connect(lambda value, p=param: self.update_slider(value, p))

            self.sliders[param] = slider
            self.slider_labels[param] = label

            h_layout.addWidget(label)
            h_layout.addWidget(slider)
            self.layout.addLayout(h_layout)

        # Button to reset particles
        self.reset_button = QPushButton("Reset Particles")
        self.layout.addWidget(self.reset_button)
        self.reset_button.clicked.connect(self.reset_particles)

        # Particle Data
        self.num_particles = self.slider_values["Particle Count"]
        self.x_data = np.random.uniform(-10, 10, self.num_particles)
        self.y_data = np.random.uniform(-10, 10, self.num_particles)

        # Scatter plot item
        self.scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush("w"))
        self.plot_widget.addItem(self.scatter)
        self.update_scatter_plot()

        # Timer for real-time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(100)

    def update_slider(self, value, param_name):
        """ Updates stored slider values and labels """
        self.slider_values[param_name] = value
        self.slider_labels[param_name].setText(f"{param_name}: {value}")
        if param_name == "Particle Count":
            self.reset_particles()  # Reset when particle count changes

    def update_particles(self):
        """ Updates particle positions using a simple random walk """
        step_size = self.slider_values["Step Size"] / 10  # Scale step size
        self.x_data += np.random.uniform(-step_size, step_size, self.num_particles)
        self.y_data += np.random.uniform(-step_size, step_size, self.num_particles)

        self.update_scatter_plot()

    def update_scatter_plot(self):
        """ Refreshes scatter plot with updated particle positions """
        self.scatter.setData(self.x_data, self.y_data)

    def reset_particles(self):
        """ Resets all particles to random positions """
        self.num_particles = self.slider_values["Particle Count"]
        self.x_data = np.random.uniform(-10, 10, self.num_particles)
        self.y_data = np.random.uniform(-10, 10, self.num_particles)
        self.update_scatter_plot()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParticleSimulation()
    window.show()
    sys.exit(app.exec())
