import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from collections import deque
import serial
from matplotlib.ticker import MultipleLocator


# Function to calculate rotation matrix from roll, pitch, and yaw
def D2R(degrees):
    return degrees * np.pi / 180

def RPY2XYZ(angles):
    roll, pitch, yaw = angles
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])
    R = np.dot(R_z, np.dot(R_y, R_x))
    return R

def cylinder_planes(coordinates):
    num_points = len(coordinates[0]) // 2
    planes = []
    for i in range(num_points):
        plane = [
            [coordinates[0][i], coordinates[0][i + num_points], coordinates[0][(i + 1) % num_points], coordinates[0][(i + 1) % num_points + num_points]],
            [coordinates[1][i], coordinates[1][i + num_points], coordinates[1][(i + 1) % num_points], coordinates[1][(i + 1) % num_points + num_points]],
            [coordinates[2][i], coordinates[2][i + num_points], coordinates[2][(i + 1) % num_points], coordinates[2][(i + 1) % num_points + num_points]]
        ]
        planes.append(plane)
    return planes

def insideAnimation(lines, planes):
    for line, plane in zip(lines, planes):
        line.set_data(plane[0], plane[1])
        line.set_3d_properties(plane[2])

def outsideAnimation(planes, ax):
    lines = []
    for plane in planes:
        line, = ax.plot(plane[0], plane[1], plane[2], linestyle='dashed')
        lines.append(line)
    return lines

def smallDetails(ax):
    ax.set_xlabel('X', fontweight="bold")
    ax.set_ylabel('Y', fontweight="bold")
    ax.set_zlabel('Z', fontweight="bold")

    # Set plot limits
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_zlim(-1, 1)

    ax.grid(False)

    # Reverse
    ax.invert_xaxis()
    ax.invert_yaxis()

    ax.xaxis.set_major_locator(MultipleLocator(0.5))
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    ax.zaxis.set_major_locator(MultipleLocator(0.5))

# Initialize lists to store sensor data
temperature_data = deque(maxlen=100)
humidity_data = deque(maxlen=100)
pressure_data = deque(maxlen=100)
altitude_data = deque(maxlen=100)
ultrasonic_data = deque(maxlen=100)
gps_data = deque(maxlen=1)

# Create main tkinter window
root = tk.Tk()
root.title("CANSAT Data Visualization")

# Create frames for better organization
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Heading
heading_label = tk.Label(left_frame, text="CANSAT Monitoring Interface", font=("Helvetica", 16, "bold"), pady=10)
heading_label.pack()

# Create figure and subplots for sensor data
fig, ((ax_temp, ax_hum), (ax_press, ax_alt)) = plt.subplots(2, 2, figsize=(10, 10))

# Temperature plot
line_temp, = ax_temp.plot([], [], label='Temperature', color='r')
ax_temp.set_xlabel('Time')
ax_temp.set_ylabel('Temperature (°C)')
ax_temp.legend()
ax_temp.grid(True)

# Humidity plot
line_humidity, = ax_hum.plot([], [], label='Humidity', color='b')
ax_hum.set_xlabel('Time')
ax_hum.set_ylabel('Humidity (%)')
ax_hum.legend()
ax_hum.grid(True)

# Pressure plot
line_press, = ax_press.plot([], [], label='Pressure', color='g')
ax_press.set_xlabel('Time')
ax_press.set_ylabel('Pressure (hPa)')
ax_press.legend()
ax_press.grid(True)

# Altitude plot
line_alt, = ax_alt.plot([], [], label='Altitude', color='m')
ax_alt.set_xlabel('Time')
ax_alt.set_ylabel('Altitude (m)')
ax_alt.legend()
ax_alt.grid(True)

# Create tkinter canvas to embed matplotlib figure
canvas = FigureCanvasTkAgg(fig, master=left_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

# Create a 3D axis for cylinder animation
fig_3d = plt.figure(figsize=(5, 5))
ax_cylinder = fig_3d.add_subplot(111, projection='3d')
canvas_3d = FigureCanvasTkAgg(fig_3d, master=right_frame)
canvas_3d.draw()
canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=1)

# Initialize cylinder points
radius = 0.2
height = 0.6
num_points = 30  # Number of points to represent the circle
theta = np.linspace(0, 2 * np.pi, num_points)
x_bottom = radius * np.cos(theta)
y_bottom = radius * np.sin(theta)
z_bottom = np.zeros(num_points)
x_top = x_bottom
y_top = y_bottom
z_top = height * np.ones(num_points)
coordinates = np.array([np.concatenate((x_bottom, x_top)),
                        np.concatenate((y_bottom, y_top)),
                        np.concatenate((z_bottom, z_top))])

lines_cylinder = outsideAnimation(cylinder_planes(coordinates), ax_cylinder)
smallDetails(ax_cylinder)

# Create labels to display GPS and ultrasonic data
gps_label = tk.Label(right_frame, text="GPS: --\nSpeed: -- knots\nAltitude: -- meters", font=("Helvetica", 14), anchor="w", justify="left")
gps_label.pack(fill=tk.BOTH, expand=1)

pressure_label = tk.Label(right_frame, text="Pressure: -- hPa", font=("Helvetica", 14), anchor="w", justify="left")
pressure_label.pack(fill=tk.BOTH, expand=1)

ultrasonic_label = tk.Label(right_frame, text="Ultrasonic: -- cm", font=("Helvetica", 14), anchor="w", justify="left")
ultrasonic_label.pack(fill=tk.BOTH, expand=1)

# Function to calculate pressure from altitude
def calculate_pressure(altitude):
    # Barometric formula to estimate pressure from altitude
    P0 = 1013.25  # sea level standard atmospheric pressure in hPa
    T0 = 288.15  # standard temperature in Kelvin
    g = 9.80665  # standard gravity
    L = 0.0065  # temperature lapse rate
    R = 287.05  # gas constant
    altitude = float(altitude)
    pressure = P0 * (1 - (L * altitude) / T0) ** (g / (R * L))
    return pressure

# Open serial connection
ser = serial.Serial('COM8', 115200, timeout=1)

# Open CSV file for writing
csv_file = open('cansat_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
# Write the header
csv_writer.writerow(['Temperature', 'Humidity', 'AngleX', 'AngleY', 'AngleZ', 'Distance', 'Latitude', 'Longitude', 'Altitude', 'Speed', 'Pressure'])

# Update plot periodically
def animate():
    try:
        data = ser.readline().decode('utf-8', errors='ignore').strip().split()
        print(data)  # Add print statement to see serial data
        if len(data) >= 10:
            temperature = float(data[0])
            humidity = float(data[1])
            angleX = float(data[2])
            angleY = float(data[3])
            angleZ = float(data[4])
            distance = float(data[5])
            latitude = float(data[6])
            longitude = float(data[7])
            altitude = float(data[8])
            speed = float(data[9])
            pressure = calculate_pressure(altitude)

            temperature_data.append(temperature)
            humidity_data.append(humidity)
            pressure_data.append(pressure)
            altitude_data.append(altitude)
            ultrasonic_data.append(distance)
            gps_data.append((latitude, longitude))

            # Write data to CSV
            csv_writer.writerow([temperature, humidity, angleX, angleY, angleZ, distance, latitude, longitude, altitude, speed, pressure])

            update_plots()

            # Update pressure label
            pressure_label.config(text=f"Pressure: {pressure:.2f} hPa")

            # Update ultrasonic label
            ultrasonic_label.config(text=f"Ultrasonic: {distance:.2f} cm")

            # Update GPS label
            gps_label.config(
                text=f"GPS:\nLat: {latitude:.6f}\nLng: {longitude:.6f}\nSpeed: {speed:.2f} knots\nAltitude: {altitude:.2f} meters")

            # Update cylinder animation
            angles = [D2R(angleX), D2R(angleY), D2R(angleZ)]
            Rotate = RPY2XYZ(angles)
            new_coordinates = np.dot(Rotate, coordinates)
            planes = cylinder_planes(new_coordinates)
            insideAnimation(lines_cylinder, planes)

            canvas_3d.draw()

        root.after(1000, animate)
    except Exception as e:
        print(f"Error: {e}")

def update_plots():
    line_temp.set_data(range(len(temperature_data)), temperature_data)
    ax_temp.relim()
    ax_temp.autoscale_view()

    line_humidity.set_data(range(len(humidity_data)), humidity_data)
    ax_hum.relim()
    ax_hum.autoscale_view()

    line_press.set_data(range(len(pressure_data)), pressure_data)
    ax_press.relim()
    ax_press.autoscale_view()

    line_alt.set_data(range(len(altitude_data)), altitude_data)
    ax_alt.relim()
    ax_alt.autoscale_view()

    canvas.draw()

# Start animation
animate()

# Close serial connection and CSV file when closing window
def on_closing():
    ser.close()
    csv_file.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
