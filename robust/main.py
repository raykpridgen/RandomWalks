from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSlider, QSpinBox, QPushButton
)
from PyQt6.QtCore import Qt
from pyqtgraph import PlotWidget # type: ignore
import pyqtgraph as pg
import sys
import subprocess
import os
import mmap
import struct
import posix_ipc
import threading
import queue
import time
import math
from datetime import datetime

SHM_NAME = "/particle_shm"

C_EXECUTABLE = "./RWoperation"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x_vals = []
        self.y_vals = []
        self.particle_count = 1000
        self.shm_fd = None
        self.shm = None
        self.process = None
        self.output_queue = queue.Queue()

        self.setWindowTitle("Particle Simulation")
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.graph_widget = PlotWidget()
        self.graph_widget.setBackground("black")
        self.graph_widget.setTitle("Particle Frequency at X Positions", color="w", size="16pt")
        self.graph_widget.showGrid(x=True, y=True)
        self.main_layout.addWidget(self.graph_widget, 2)

        self.control_panel = QGroupBox("Simulation Parameters")
        self.control_layout = QFormLayout()
        self.control_panel.setLayout(self.control_layout)
        self.main_layout.addWidget(self.control_panel, 1)

        # Input widgets
        self.dt_input = QLineEdit("1")
        self.D_input = QLineEdit("1")
        self.T_slider = QSpinBox()
        self.T_slider.setRange(10, 10000)
        self.T_slider.setValue(1000)

        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(0)
        self.b_value_label = QLabel("0.00")  # Label to display b value

        self.g_slider = QSlider(Qt.Orientation.Horizontal)
        self.g_slider.setRange(0, 100)
        self.g_slider.setValue(10)
        self.g_value_label = QLabel("0.10")  # Label to display g value

        self.particles_slider = QSlider(Qt.Orientation.Horizontal)
        self.particles_slider.setRange(1, 100000)
        self.particles_slider.setValue(self.particle_count)
        self.particles_value_label = QLabel(str(self.particle_count))  # Label to display particles value

        # Connect sliders to update their labels
        self.b_slider.valueChanged.connect(self.update_b_label)
        self.g_slider.valueChanged.connect(self.update_g_label)
        self.particles_slider.valueChanged.connect(self.update_particles_label)

        # Add widgets to layout with labels
        self.control_layout.addRow(QLabel("dt:"), self.dt_input)
        self.control_layout.addRow(QLabel("T:"), self.T_slider)
        self.control_layout.addRow(QLabel("D:"), self.D_input)
        
        b_layout = QHBoxLayout()
        b_layout.addWidget(self.b_slider)
        b_layout.addWidget(self.b_value_label)
        self.control_layout.addRow(QLabel("b:"), QWidget())
        self.control_layout.addRow(b_layout)

        g_layout = QHBoxLayout()
        g_layout.addWidget(self.g_slider)
        g_layout.addWidget(self.g_value_label)
        self.control_layout.addRow(QLabel("g:"), QWidget())
        self.control_layout.addRow(g_layout)

        particles_layout = QHBoxLayout()
        particles_layout.addWidget(self.particles_slider)
        particles_layout.addWidget(self.particles_value_label)
        self.control_layout.addRow(QLabel("Particles:"), QWidget())
        self.control_layout.addRow(particles_layout)

        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.resetButton)
        self.control_layout.addRow(self.reset_button)

        self.curve = self.graph_widget.plot(self.x_vals, self.y_vals, pen=None, symbol='o', symbolSize=5, symbolBrush='purple')
        self.solCurve = self.graph_widget.plot([], [], pen='y', symbol='o', symbolSize=5, symbolBrush='y')
        #self.solutionCurve = 
        self.initialize_shared_memory()
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

    def update_b_label(self, value):
        """Update the label for b slider with its current value."""
        self.b_value_label.setText(f"{value / 100:.2f}")

    def update_g_label(self, value):
        """Update the label for g slider with its current value."""
        self.g_value_label.setText(f"{value / 100:.2f}")

    def update_particles_label(self, value):
        """Update the label for particles slider with its current value."""
        self.particles_value_label.setText(str(value))

    def resetButton(self):
        """Handle reset button click: start simulation and let timer handle plotting."""
        self.last_particle_data = None
        self.reset_simulation()
        # Milliseconds
        self.timer.start(50)

    def initialize_shared_memory(self):

        self.particle_count = self.particles_slider.value()
        size = 12 + self.particle_count * 8
        self.shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT | posix_ipc.O_RDWR, size=size)
        self.shm_buf = mmap.mmap(self.shm.fd, size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)

        self.shm_buf[4:8] = struct.pack('i', self.particle_count)
        offset = 12
        for i in range(self.particle_count):
            self.shm_buf[offset:offset+4] = struct.pack('f', float(i % 2))
            self.shm_buf[offset+4:offset+8] = struct.pack('f', 0.0)
            offset += 8

        self.shm_buf[0:4] = struct.pack('i', 1)

    def read_output(self, pipe, label):
        for line in iter(pipe.readline, ''):
            self.output_queue.put(f"{label}: {line.strip()}")
        pipe.close()

    def reset_simulation(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("Terminated previous C process.")

        self.cleanup_shared_memory()
        self.initialize_shared_memory()

        dt = self.dt_input.text()
        T = self.T_slider.value()
        D = self.D_input.text()
        b = self.b_slider.value() / 100.0
        g = self.g_slider.value() / 100.0
        particles = self.particles_slider.value()
        cores = 20

        if not os.path.exists(C_EXECUTABLE):
            print(f"Error: {C_EXECUTABLE} not found. Please compile it first.")
            return

        command = [C_EXECUTABLE, str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        threading.Thread(target=self.read_output, args=(self.process.stdout, "C Output"), daemon=True).start()
        threading.Thread(target=self.read_output, args=(self.process.stderr, "C Error"), daemon=True).start()

    def read_shared_memory(self):
        start_time = time.time() * 1000
           
        # If flag is still one from when python last operated
        if struct.unpack('i', self.shm_buf[0:4])[0] != 0:
            return []
        count = struct.unpack('i', self.shm_buf[4:8])[0]
        topParticles = {}
        bottomParticles = {}
        offset = 12
        minX = 0
        maxX = 0
        
        for _ in range(count):
            x = struct.unpack('f', self.shm_buf[offset:offset+4])[0]
            y = struct.unpack('f', self.shm_buf[offset+4:offset+8])[0]
            
            if x > maxX:
                maxX = x
            if x < minX:
                minX = x

            if y == 1:
                topParticles[x] = topParticles.get(x, 0) + 1
            else:
                bottomParticles[x] = bottomParticles.get(x, 0) + 1
            
            offset += 8
        
        moveDistance = math.sqrt(2 * float(self.D_input.text()) * float(self.dt_input.text()))

        particles = []   
        for x in set(topParticles.keys()) | set(bottomParticles.keys()):  # Fixed typo
            if x in topParticles:
                yPart = topParticles[x] / count
                particles.append((x * moveDistance, yPart)) 
            if x in bottomParticles:
                yPart = bottomParticles[x] / count
                particles.append((x * moveDistance, -1 * yPart))

        self.shm_buf[0:4] = struct.pack('i', 1)
        newParts = [(x, y) for x, y in particles if not (x == 0 and y == 0)]
        
        return newParts

    def analyticSolution(self, x, t, v, D=1):    
        lead = 1 / math.sqrt(4 * math.pi * D * t)
        exponent = -1 * ((x - (v * t)) ** 2)/(4 * D * t)
        return lead * (math.e ** exponent)
    
    def solutionCurve(self, minX, maxX):
        solutionVals = []
        timeIter = self.T_slider.value() / float(self.dt_input.text())
        fudgeFactor = 1 #math.sqrt(8*float(self.dt_input.text()))
        print(f"Time used: {timeIter}\n") 
        for x in range(int(minX), int(maxX)):
            y = self.analyticSolution(x, timeIter, self.b_slider.value(), float(self.D_input.text()))
            solutionVals.append((x, y / fudgeFactor))
        for x in range(int(minX), int(maxX)):
            y = self.analyticSolution(x, timeIter, self.b_slider.value(), float(self.D_input.text()))
            solutionVals.append((x, -y / fudgeFactor))
            
        return solutionVals
    
    def update_plot(self):
        while not self.output_queue.empty():
            print(self.output_queue.get())

        if self.process is not None and self.process.poll() is None:
            particles = self.read_shared_memory()
            if particles:
                self.x_vals, self.y_vals = zip(*particles)
                solution = self.solutionCurve(min(self.x_vals), max(self.x_vals))
                self.x_vals_sol, self.y_vals_sol = zip(*solution)
                self.curve.setData(self.x_vals, self.y_vals)
                self.solCurve.setData(self.x_vals_sol, self.y_vals_sol)
        elif self.process is not None and self.process.poll() is not None:
            self.timer.stop()
            while not self.output_queue.empty():
                print(self.output_queue.get())
            print("C process has terminated.")

    def cleanup_shared_memory(self):
        # Shared memory cleanup
        if hasattr(self, 'shm_buf') and self.shm_buf is not None:
            try:
                self.shm_buf.close()  # Close mmap buffer
            except Exception as e:
                print(f"Error closing shm_buf: {e}")
            finally:
                self.shm_buf = None

        if hasattr(self, 'shm') and self.shm is not None:
            try:
                posix_ipc.unlink_shared_memory(SHM_NAME)  # Remove from system
            except posix_ipc.ExistentialError:
                print("Shared memory already unlinked")
            except Exception as e:
                print(f"Shared memory cleanup error: {e}")
            finally:
                self.shm = None

    def closeEvent(self, event):
        print("Shutting down simulation...")
        self.timer.stop()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.cleanup_shared_memory()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 