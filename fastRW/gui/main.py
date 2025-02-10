from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFormLayout, 
    QGroupBox, QLabel, QLineEdit, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import numpy as np
import subprocess
import sysv_ipc
import struct
import ctypes
import os
import mmap


# Define the DataParticle structure
class DataParticle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("freqx", ctypes.c_float),
    ]

# Define the ParticleDataList structure
class ParticleDataList(ctypes.Structure):
    _fields_ = [
        ("particles", DataParticle * 325),  # Array of 325 DataParticle structures
        ("count", ctypes.c_int),            # Integer field
        ("read", ctypes.c_bool),            # Boolean field
    ]

class MainWindow(QMainWindow):

    SHM_NAME = "/particle_shm"
    PARTICLE_COUNT = 325
    STRUCT_FORMAT = f"{PARTICLE_COUNT * 3}f ii"
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(self):
        super().__init__()
        self.xVals = []
        self.yVals = []
        self.freqVals = []

        # Window properties
        self.setWindowTitle("Particle Simulation")
        self.setGeometry(100, 100, 1000, 600)  # Wider window for control panel

        # Main layout (horizontal: Graph on left, controls on right)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # === LEFT: Graph ===
        self.graphWidget = PlotWidget()
        self.graphWidget.setBackground("black")
        self.graphWidget.setTitle("Real-Time Particle Simulation", color="w", size="16pt")
        self.graphWidget.showGrid(x=True, y=True)
        self.main_layout.addWidget(self.graphWidget, 2)  # Graph takes 2/3 of space

        # === RIGHT: Controls ===
        self.control_panel = QGroupBox("Simulation Parameters")
        self.control_layout = QFormLayout()
        self.control_panel.setLayout(self.control_layout)
        self.main_layout.addWidget(self.control_panel, 1)  # Controls take 1/3 of space

        # === INPUT FIELDS ===
        self.dt_input = QLineEdit("1")  # dt: Default 1
        self.D_input = QLineEdit("1")  # D: Default 1 (precise input)
        
        # === SLIDERS / SPINBOXES ===
        self.T_slider = QSpinBox()  # T: Integer, fast adjustment
        self.T_slider.setRange(10, 10000)
        self.T_slider.setValue(10)

        self.b_slider = QSlider(Qt.Orientation.Horizontal)  # b: -1 to 1
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(0)

        self.g_slider = QSlider(Qt.Orientation.Horizontal)  # g: 0 to 1 (or later 0-0.15)
        self.g_slider.setRange(0, 100)  # Maps to 0.00 - 1.00
        self.g_slider.setValue(0)

        self.particles_slider = QSlider(Qt.Orientation.Horizontal)  # Particles: Up to 100,000
        self.particles_slider.setRange(1, 100000)
        self.particles_slider.setValue(200)

        # === ADD TO CONTROL PANEL ===
        self.control_layout.addRow(QLabel("dt:"), self.dt_input)
        self.control_layout.addRow(QLabel("T:"), self.T_slider)
        self.control_layout.addRow(QLabel("D:"), self.D_input)
        self.control_layout.addRow(QLabel("b:"), self.b_slider)
        self.control_layout.addRow(QLabel("g:"), self.g_slider)
        self.control_layout.addRow(QLabel("Particles:"), self.particles_slider)

        # === RESET BUTTON ===
        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.control_layout.addRow(self.reset_button)

        # === PLOTTING LOGIC ===
        self.curve = self.graphWidget.plot(self.xVals, self.yVals, pen=None, symbol='o', symbolSize=5, symbolBrush='y')

        print("Before sim reset\n")
        self.reset_simulation()
        self.timer = pg.QtCore.QTimer()
        
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50) # 50 ms ticks

    def reset_simulation(self):
        print("reset_simulation\n")
        dt = self.dt_input.text()  # QLineEdit text
        T = self.T_slider.value()  # QSpinBox value
        D = self.D_input.text()  # QLineEdit text
        b = self.b_slider.value()  # QSlider value
        g = self.g_slider.value()  # QSlider value
        particles = self.particles_slider.value()  # QSlider value
        cores = 4
        command = [
            "./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)
        ]
        print("C program was called\n")
        print(command)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #for line in self.process.stdout:
        #    print(f"C Output: {line.decode('utf-8').strip()}")

    

    def read_shared_memory(self):
        print("read_shared_memory\n")
        """ Reads complex data structure from shared memory. """
        # Try to open shared memory
        try:
            shm_fd = os.open(f"/dev/shm{self.SHM_NAME}", os.O_RDWR)
            shm = mmap.mmap(shm_fd, self.STRUCT_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        except FileNotFoundError:
            raise FileNotFoundError("Shared memory does not exist.\n")
        
        # Read flag
        read_offset = self.STRUCT_SIZE - 4
        current_read = struct.unpack("i", shm[read_offset:read_offset + 4])[0]
        if current_read % 2 == 1:
                        
            shm.close()
            os.close(shm_fd)
            return [], current_read, []

        # Unpack particles
        num_floats = self.PARTICLE_COUNT * 3
        STRUCT_FORMAT_PARTICLES = f"{num_floats}f"
        particles = struct.unpack(STRUCT_FORMAT_PARTICLES, shm[:num_floats * 4])

        # Make particles list
        particles_list = [particles[i:i+3] for i in range(0, len(particles), 3)]
        
        new_read = current_read + 1

        shm[read_offset:read_offset + 4] = struct.pack("i", new_read)
        shm.flush()
        shm.close()
        os.close(shm_fd)

        return len(particles), new_read, particles_list

    def update_plot(self):
        print("update_plot\n")
        """ Fetch new data from C and update the graph """
        
        if self.process.poll() is not None: 
            self.timer.stop()  # This will stop the timer from triggering the update function
            print("C process ended.\n")
            stdout, stderr = self.process.communicate()  # This will block until the process finishes

            # Decode byte output to strings
            stdout_decoded = stdout.decode("utf-8")
            stderr_decoded = stderr.decode("utf-8")

            print(f"Output: {stdout_decoded}\n")
            print(f"Error: {stderr_decoded}\n")

            return 0

        # Read shared memory if C is running
        count, read_flag, particles = self.read_shared_memory()

        # If data has not been read by Python
        if read_flag % 2 == 0:  # Only update if 'read' flag is not set, ie new
            print("flag coming out of read_shared_memory says false, processing data\n")
            # Optionally, update the plot with multiple curves (one for each attribute)
            # You can plot `x` vs `y` and `x` vs `freqx`, or overlay all in a single plot

            self.xVals = []
            self.yVals = []
            self.freqVals = []

            for x, y, freq in particles:
                self.xVals.append(x)
                self.yVals.append(y)
                self.freqVals.append(freq)

            # Example of setting the data for plotting (you may want multiple plots or combine them)
            # If you want to plot freqx as a separate curve, you can add another curve:
            # self.curve_freqx.setData(self.x, self.freqx)
            # Process output (assuming space-separated values)

            if not self.xVals or not self.yVals:
                print("Error: x or y values are empty!")
                return  # Early exit if data is invalid
            try:
                self.curve.setData(self.xVals, self.freqVals) 
            except ValueError:
                print("Invalid data from C program.")
        else:
            return 0
        
    def closeEvent(self, event):
        """ Cleanup resources when closing the application """
        print("Shutting down simulation...")

        # Stop update timer
        self.timer.stop()

        # Terminate C program if running
        if self.process and self.process.poll() is None:
            self.process.terminate()  # Gracefully terminate
            
            print("Terminating subprocess...")
            print("C process ended.\n")
            stdout, stderr = self.process.communicate()  # This will block until the process finishes

            # Decode byte output to strings
            stdout_decoded = stdout.decode("utf-8")
            stderr_decoded = stderr.decode("utf-8")

            print(f"Output: {stdout_decoded}\n")
            print(f"Error: {stderr_decoded}\n")
            
            
            
            try:
                self.process.wait(timeout=2)  # Wait up to 2 sec
            except subprocess.TimeoutExpired:
                print("Forcing subprocess termination...")
                self.process.kill()  # Kill if it hangs


        event.accept()  # Allow window to close


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
