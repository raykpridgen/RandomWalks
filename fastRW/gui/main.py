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
import mmap
import struct
import os
import time


class MainWindow(QMainWindow):

    SHM_SIZE = 1208  # Define the shared memory size in bytes. Adjust as necessary.
    SHM_KEY = 4755

    def __init__(self):
        super().__init__()
        self.xVals = []
        self.yVals = []
        self.freqVals = []
        
        # Setup shared memory (key should match C program)
        self.shm = sysv_ipc.SharedMemory(self.SHM_KEY, sysv_ipc.IPC_CREAT, size=self.SHM_SIZE)
        #self.flag_shm = sysv_ipc.SharedMemory(self.SHM_SIZE)  # Separate flag memory (if used)

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
        self.T_slider.setValue(1000)

        self.b_slider = QSlider(Qt.Orientation.Horizontal)  # b: -1 to 1
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(0)

        self.g_slider = QSlider(Qt.Orientation.Horizontal)  # g: 0 to 1 (or later 0-0.15)
        self.g_slider.setRange(0, 100)  # Maps to 0.00 - 1.00
        self.g_slider.setValue(0)

        self.particles_slider = QSlider(Qt.Orientation.Horizontal)  # Particles: Up to 100,000
        self.particles_slider.setRange(1, 100000)
        self.particles_slider.setValue(1000)

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
            "sudo", "./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)
        ]
        print("C program was called\n")
        print(command)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #for line in self.process.stdout:
        #    print(f"C Output: {line.decode('utf-8').strip()}")

    

    def read_shared_memory(self):
        print("read_shared_memory\n")
        """ Reads complex data structure from shared memory. """
        raw_data = self.shm.read(self.SHM_SIZE)
        
        # Unpack the data:
        # First unpack the count (4 bytes) and read flag (1 byte)
        count, read_flag = struct.unpack("I?", raw_data[:5])  # "I" for int (count), "?" for bool (read)
        if not read_flag:
            print("python reads flag as false, begins reading data\n")
            # Unpack the particles array (each particle = 3 floats, 12 bytes each)
            num_particles = 325
            particle_format = "3f"  # Three floats for each DataParticle (x, y, freqx)
            particles = []
            offset = 5  # Start after the count and read flag (5 bytes)

            for i in range(num_particles):
                # Unpack each DataParticle (x, y, freqx)
                particle_data = struct.unpack_from(particle_format, raw_data, offset)
                particles.append(particle_data)
                offset += struct.calcsize(particle_format)  # Move to the next DataParticle

            
            new_data = struct.pack("I?", count, True)

            self.shm.write(new_data)
            print("Memory was available\n")
            return count, read_flag, particles
        else:
            print("No memory available\n")
            print(f"Read flag: {read_flag}")
            return [], read_flag, []

    def update_plot(self):
        print("update_plot\n")
        """ Fetch new data from C and update the graph """
        
        if self.process.poll() is not None: 
            self.timer.stop()  # This will stop the timer from triggering the update function
            print("C process ended\n")
            return 0

        # Read shared memory if C is running
        count, read_flag, particles = self.read_shared_memory()

        # If data has not been read by Python
        if not read_flag:  # Only update if 'read' flag is not set, ie new
            print("flag coming out of read_shared_memory says false, processing data\n")
            # Optionally, update the plot with multiple curves (one for each attribute)
            # You can plot `x` vs `y` and `x` vs `freqx`, or overlay all in a single plot

            self.xVals = [p[0] for p in particles]  # Extract x values from particles
            self.yVals = [p[1] for p in particles]  # Extract y values from particles
            self.freqVals = [p[2] for p in particles]  # Extract freqx values from particles

            print(f"x values: {self.xVals}\n")
            print(f"y values: {self.yVals}\n")
            
            # Example of setting the data for plotting (you may want multiple plots or combine them)
            # If you want to plot freqx as a separate curve, you can add another curve:
            # self.curve_freqx.setData(self.x, self.freqx)
            # Process output (assuming space-separated values)

            if not self.xVals or not self.yVals:
                print("Error: x or y values are empty!")
                return  # Early exit if data is invalid
            try:
                self.curve.setData(self.xVals, self.yVals)  # Plot x vs y
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
            print("Terminating subprocess...")
            self.process.terminate()  # Gracefully terminate
            try:
                self.process.wait(timeout=2)  # Wait up to 2 sec
            except subprocess.TimeoutExpired:
                print("Forcing subprocess termination...")
                self.process.kill()  # Kill if it hangs

        # Close shared memory
        self.shm.detach()  # Detach from SysV shared memory

        event.accept()  # Allow window to close


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
