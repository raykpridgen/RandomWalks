from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSlider, QSpinBox, QPushButton
)
from PyQt6.QtCore import Qt
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import numpy as np
import subprocess
import os
import mmap
import struct
import posix_ipc  # For POSIX semaphores (install with `pip install posix-ipc`)

SHM_NAME = "/particle_shm"
SEM_NAME = "/particle_sem"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x_vals = []
        self.y_vals = []
        self.particle_count = 1000  # Default, adjustable via slider
        self.shm_fd = None
        self.shm = None
        self.sem = None

        # Window properties
        self.setWindowTitle("Particle Simulation")
        self.setGeometry(100, 100, 1000, 600)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Left: Graph
        self.graph_widget = PlotWidget()
        self.graph_widget.setBackground("black")
        self.graph_widget.setTitle("Real-Time Particle Simulation", color="w", size="16pt")
        self.graph_widget.showGrid(x=True, y=True)
        self.main_layout.addWidget(self.graph_widget, 2)

        # Right: Controls
        self.control_panel = QGroupBox("Simulation Parameters")
        self.control_layout = QFormLayout()
        self.control_panel.setLayout(self.control_layout)
        self.main_layout.addWidget(self.control_panel, 1)

        # Input fields
        self.dt_input = QLineEdit("1")
        self.D_input = QLineEdit("1")
        self.T_slider = QSpinBox()
        self.T_slider.setRange(10, 10000)
        self.T_slider.setValue(10)
        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(0)
        self.g_slider = QSlider(Qt.Orientation.Horizontal)
        self.g_slider.setRange(0, 100)
        self.g_slider.setValue(0)
        self.particles_slider = QSlider(Qt.Orientation.Horizontal)
        self.particles_slider.setRange(1, 100000)
        self.particles_slider.setValue(self.particle_count)

        # Add to control panel
        self.control_layout.addRow(QLabel("dt:"), self.dt_input)
        self.control_layout.addRow(QLabel("T:"), self.T_slider)
        self.control_layout.addRow(QLabel("D:"), self.D_input)
        self.control_layout.addRow(QLabel("b:"), self.b_slider)
        self.control_layout.addRow(QLabel("g:"), self.g_slider)
        self.control_layout.addRow(QLabel("Particles:"), self.particles_slider)

        # Reset button
        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.control_layout.addRow(self.reset_button)

        # Plotting
        self.curve = self.graph_widget.plot(self.x_vals, self.y_vals, pen=None, symbol='o', symbolSize=5, symbolBrush='y')

        # Initialize shared memory and semaphore
        self.initialize_shared_memory()
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)  # 50ms ticks

    def initialize_shared_memory(self):
        """Initialize shared memory and semaphore for C to attach to."""
        self.particle_count = self.particles_slider.value()
        size = 4 + self.particle_count * 8  # sizeof(int) + sizeof(Particle) * count

        # Create shared memory
        self.shm_fd = os.open(SHM_NAME, os.O_CREAT | os.O_RDWR, 0o666)
        os.ftruncate(self.shm_fd, size)
        self.shm = mmap.mmap(self.shm_fd, size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)

        # Write initial count
        self.shm[0:4] = struct.pack('i', self.particle_count)

        # Create semaphore (starts at 0, Python waits for C)
        self.sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREAT, initial_value=0)

    def reset_simulation(self):
        """Launch C program with parameters."""
        dt = self.dt_input.text()
        T = self.T_slider.value()
        D = self.D_input.text()
        b = self.b_slider.value() / 100.0  # Scale to -1 to 1
        g = self.g_slider.value() / 100.0  # Scale to 0 to 1
        particles = self.particles_slider.value()
        cores = 4  # Example, adjust as needed

        # If particle count changed, reinitialize shared memory
        if particles != self.particle_count:
            self.cleanup_shared_memory()
            self.initialize_shared_memory()

        command = ["./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)]
        print(f"Calling C program: {' '.join(command)}")
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def read_shared_memory(self):
        """Read particle data from shared memory."""
        self.sem.acquire()  # Wait for C to signal

        count = struct.unpack('i', self.shm[0:4])[0]
        particles = []
        offset = 4
        for _ in range(count):
            x = struct.unpack('f', self.shm[offset:offset+4])[0]
            y = struct.unpack('f', self.shm[offset+4:offset+8])[0]
            particles.append((x, y))
            offset += 8

        self.sem.release()  # Signal C to continue
        return particles

    def update_plot(self):
        """Fetch new data from C and update the graph."""
        if hasattr(self, 'process') and self.process.poll() is not None:
            self.timer.stop()
            stdout, stderr = self.process.communicate()
            print(f"C Output: {stdout.decode('utf-8')}")
            print(f"C Error: {stderr.decode('utf-8')}")
            return

        particles = self.read_shared_memory()
        self.x_vals, self.y_vals = zip(*particles) if particles else ([], [])
        if self.x_vals and self.y_vals:
            self.curve.setData(self.x_vals, self.y_vals)

    def cleanup_shared_memory(self):
        """Clean up shared memory and semaphore."""
        if self.shm:
            self.shm.close()
        if self.shm_fd:
            os.close(self.shm_fd)
        if os.path.exists(f"/dev/shm{SHM_NAME}"):
            os.unlink(f"/dev/shm{SHM_NAME}")
        if self.sem:
            self.sem.close()
            self.sem.unlink()

    def closeEvent(self, event):
        """Cleanup on window close."""
        print("Shutting down simulation...")
        self.timer.stop()
        if hasattr(self, 'process') and self.process.poll() is None:
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