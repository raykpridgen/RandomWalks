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

    SHM_SIZE = 3908  # Define the shared memory size in bytes. Adjust as necessary.
    SHM_KEY = 4755

    particle_count = 325
    particle_format = "fff"  # Format for one particle (float x, y, freqx)
    particle_list_format = f"{particle_count * 3}f i 3x ?" 

    def __init__(self):
        super().__init__()
        self.xVals = []
        self.yVals = []
        self.freqVals = []
        
        # Setup shared memory (key should match C program)
        try:
            # Open the shared memory segment
            self.shm = sysv_ipc.SharedMemory(self.SHM_KEY)
        except sysv_ipc.ExistentialError:
            print("Shared memory segment not found.")
            exit(1)

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
        buffer = self.shm.read()
        if len(buffer) != ctypes.sizeof(ParticleDataList):
            raise RuntimeError(f"Shared memory size mismatch: expected {ctypes.sizeof(ParticleDataList)}, got {len(buffer)}")

        unpacked = struct.unpack(self.particle_list_format, buffer)

        count = unpacked[self.particle_count * 3]
        read_flag = unpacked[self.particle_count * 3 + 1]

        print(f"Count: {count}")
        print(f"Read: {read_flag}")

        # Unpack the data:
        if not read_flag:
            print("python reads flag as false, begins reading data\n")

            newParticles = []

            check = False

            for i in range(count):
                x, y, freqx = unpacked[i * 3 : (i * 3) + 3]
                if freqx[i] > 0:
                    check = True
                newParticles.extend([x, y, freqx])
                
            sendSetup = ParticleDataList()
            sendSetup.read = True
            self.shm.write(bytearray(sendSetup))

            buffer = self.shm.read()
            updated_data = ParticleDataList.from_buffer_copy(buffer)

            print("Updated read flag:", updated_data.read)
            
            if not check:
                print("No data in incoming list. returning.\n")
                return [], read_flag, []

            
            print("Memory was available\n")
            return count, False, newParticles
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

            self.xVals = []
            self.yVals = []
            self.freqVals = []

            for l in particles:
                self.xVals, self.yVals, self.freqVals = particles[l * 3 : (l * 3) + 3]
            
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
