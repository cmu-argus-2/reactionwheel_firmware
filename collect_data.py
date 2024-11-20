# Full disclosure: Quick script written by ChatGPT.

import serial
import csv

def read_serial_data(port, baudrate):
    """
    Reads and parses lines of floating-point data from a serial port.

    Args:
        port (str): The serial port to connect to (e.g., 'COM3', '/dev/ttyUSB0').
        baudrate (int): The baud rate for the serial connection.
    """
    try:
        # Open the serial connection
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"Connected to {port} at {baudrate} baud.")

            # Create a collection of lines. Could make this a queue and
            # asynchronously write to disk in another thread later.
            measurements = []
            while True:
                # Read a line from the serial port
                line = ser.readline().decode('utf-8').strip()

                if line:
                    try:
                        # Parse the line into a list of floating-point numbers
                        values = [float(value) for value in line.split()]

                        # Ensure the line contains exactly 7 values
                        if len(values) == 7:
                            print(f"Received: {values}")
                            # print(f"Values: {values}")
                            measurements.append(values)
                        else:
                            print(f"Invalid line (wrong number of values): {line}")
                    except ValueError:
                        print(f"Invalid line (could not parse floats): {line}")

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Program terminated.")
        # Before exiting, write the collected values to a csv file.
        with open("hdd-measurements.csv", 'w', newline='') as csvfile:
            measurement_writer = csv.writer(csvfile)
            measurement_writer.writerows(measurements)

# Replace with your serial port and baud rate
if __name__ == "__main__":
    read_serial_data(port="COM6", baudrate=115200)
