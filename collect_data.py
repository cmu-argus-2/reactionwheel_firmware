# Full disclosure: Quick script written by ChatGPT.

import serial
import csv
from time import sleep
from typing import List

# TODO: Could create two threads:
# One spins at a provided rate to send commands (I.e., how long each sweep value
# should last for), and then the other spins at another rate (some sampling
# rate, could just be as fast as possible) to read data from the controller.

# TODO: Consider making a shared variable between the send and receive threads
# so that we can record what speed is commanded versus the actual measured
# angular speed.

# TODO: Consider just creating a class that these functions both belong to, and
# then just used an instance variable to share that data. Can instantiate this
# object in the main below, add checks outside for parsing all those parameters,
# etc.

def command_angular_speed_sweep(serial_connection:  serial.Serial,
                                start_speed_rad_s: int,
                                end_speed_rad_s: int,
                                speed_step_rad_s: int,
                                step_duration_ms: int) -> None:
  """Commands a sequence of angular speeds to the provided serial connection
  separated by step_duration milliseconds.

  Args:
      serial_connection (serial.Serial): Serial connection each commanded speed
      will be sent to.
      start_speed_rad_s (int): The first commanded angular speed.
      end_speed_rad_s (int): The angular speed that will be commanded last.
      speed_step_rad_s (int): The change in angular speed between steps.
      step_duration_ms (int): How long (in milliseconds) each angular speed
      between start and end the reaction wheel will be commanded to run at.
  """

  # TODO: First, generate a range of values from the start and end speed. Add
  # some quick checks to make sure the values provided are reasonable.
  MINIMUM_STEP_DURATION_MS = 1
  assert(step_duration_ms >= MINIMUM_STEP_DURATION_MS)
  step_duration_s = step_duration_ms / 1000
  # TODO: Next, create a for loop to loop through all the values in the range
  # that we want to command.
  for speed in range(start_speed_rad_s, end_speed_rad_s, speed_step_rad_s):
    serial_connection.write(f"T: {speed}")
    sleep(step_duration_s)

  print(f"Angular speed sweep thread completed!")


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

            # TODO: Will use the serial connection we create for both sending
            # out the commanded sweep values and receiving messages.

            # Create a collection of lines. Could make this a queue and
            # asynchronously write to disk in another thread later.
            measurements = []
            while True:
                # Read a line from the serial port
                # TODO: Determine if readline is blocking or not.
                line = ser.readline().decode('utf-8').strip()

                if line:
                    try:
                        # Parse the line into a list of floating-point numbers
                        values = [float(value) for value in line.split()]

                        # TODO: write a function to filter out values we don't
                        # care about / should reject.

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
