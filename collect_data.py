"""Script for monitoring and commanding the reaction wheel through a range of
angular speeds.
"""

import argparse
from pathlib import Path
import re
import serial
import csv
from time import sleep
from typing import List
import threading
import numpy as np
from tqdm import tqdm
import pandas as pd

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

# Great resource for python thread tutorials:
# https://superfastpython.com/thread-pipeline/ (James Brownlee)

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
    # Rewrite to use tqdm for progress bar.

    for speed in tqdm(np.arange(start_speed_rad_s, end_speed_rad_s, speed_step_rad_s)):
        tqdm.write(f"Commanding speed: {speed}")
        serial_connection.write(f"T{speed}\n".encode("utf-8"))
        sleep(step_duration_s)

    print(f"Angular speed sweep thread completed!")

def monitor_reaction_wheel(serial_connection: serial.Serial,
                           line_filter_regex: str,
                           collected_measurements: List[float],
                           sentinel: threading.Event) -> None:
    """Reads and parses lines of floating-point data from a serial port.

    Args:
        serial_connection (serial.Serial): The serial connection to read data
        from.
        line_filter_regex (str): A regular expression to filter out lines that
        contain values we don't care about. If a line matches this regular
        expression, it will be rejected.
        collected_measurements (List[List[float]]): A list of lists of
        floating-point values read from the serial connection.
    """
    while True:
        # First, check if the commander has finished. If so, no need to keep
        # reading.
        if sentinel.is_set():
            print(f"Monitor thread received sentinel. Exiting.")
            break

        # Read a line from the serial port
        line = serial_connection.readline().decode('utf-8').strip()
        if line:
            try:
                # Parse the line into a list of floating-point numbers
                values = [float(value) for value in line.split()]

                # Use the provided regular expression to filter out lines we
                # don't care about.
                if re.match(line_filter_regex, line):
                    print(f"Rejected line: {line}")
                    continue

                # TODO: Maybe also just add a simple filter here to make sure
                # the values extracted are all floats. If not, reject the line.
                if not all(isinstance(value, float) for value in values):
                    print(f"Invalid line (could not parse floats): {line}")
                    continue

                # Ensure the line contains exactly 7 values
                if len(values) == 7:
                    # print(f"Received: {values}")
                    collected_measurements.append(values)
                else:
                    # print(f"Invalid line (wrong number of values): {line}")
                    pass
            except ValueError:
                print(f"Invalid line (could not parse floats): {line}")


if __name__ == "__main__":

    # Use argparse to set up a quick CLI for grabbing parameters for our
    # functions.
    parser = argparse.ArgumentParser(description="Monitor and command the reaction wheel.")
    parser.add_argument("--port", type=str, help="The serial port to connect to.", default="COM6")
    parser.add_argument("--baudrate", type=int, help="The baud rate for the serial connection.", default=115200)
    parser.add_argument("--start_speed_rad_s", type=int, help="The first commanded angular speed in rad/s.", default=6.28)
    parser.add_argument("--end_speed_rad_s", type=int, help="The last commanded angular speed in rad/s.", default=100)
    parser.add_argument("--speed_step_rad_s", type=int, help="The change in angular speed between steps in rad/s.", default=5)
    parser.add_argument("--step_duration_ms", type=int, help="The duration of each step in milliseconds.", default=2000)
    parser.add_argument("--output_directory", type=str, help="The directory to save the output files to.", default=".")
    args = parser.parse_args()

    # TODO: Add checks for the provided parameters.

    # Check if the provided output directory exists. Throw exception if it does
    # not exist.
    output_directory = Path(args.output_directory)
    if not output_directory.exists():
        raise FileNotFoundError(f"Output directory {output_directory} does not exist.")


    # Define the default regular expression to filter out lines we don't care
    # about. By default, we mainly want to reject lines that contain "Target,"
    # as these are responses to the commands we send.
    line_filter_regex = ".*T.*"

    # Create the measurements list to store the data we read from the serial
    # connection.
    collected_measurements = []

    # Create a sentinel variable to tell the monitor thread to stop reading
    # from the serial port once the commander thread has finished. The main
    # thread will set this and the monitor thread will check it at each
    # iteration to figure out if it's time to stop. Not threadsafe but not
    # critical. threading.Event might be a better choice.
    commander_done = threading.Event()

    # TODO: Open the specified serial port with the specified baud rate.
    try:
        with serial.Serial(args.port, args.baudrate, timeout=1) as ser:
            print(f"Connected to {args.port} at {args.baudrate} baud.")

            # Create a commander thread.
            commander_thread = threading.Thread(target=command_angular_speed_sweep,
                                                args=(ser, args.start_speed_rad_s, args.end_speed_rad_s,
                                                    args.speed_step_rad_s, args.step_duration_ms))

            # Create a monitor thread.
            monitor_thread = threading.Thread(target=monitor_reaction_wheel,
                                            args=(ser, line_filter_regex, collected_measurements, commander_done))

            # Start the monitor and commander threads.
            monitor_thread.start()
            commander_thread.start()

            # Wait for the commander thread to finish.
            commander_thread.join()
            # Set the sentinel variable to tell the monitor thread to stop.
            commander_done.set()
            # Wait for the monitor thread to finish.
            monitor_thread.join()

            print(f"The commander and monitor threads completed successfully.")

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        commander_done.set()
        exit(1)
    except KeyboardInterrupt:
        print("Program terminated.")
        commander_done.set()
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        commander_done.set()
        exit(1)

    # Next, write the collected measurements to a CSV file.
    # First, create a CSV file to write the measurements to in the provided
    # output directory.
    # Define a header row for the CSV file.
    header = ["_MON_TARGET", "_MON_VOLT_Q", "_MON_VOLT_D", "_MON_CURR_Q", "_MON_CURR_D", "_MON_VEL", "_MON_ANGLE"]
    # Create a pandas dataframe from the collected measurements.
    df = pd.DataFrame(collected_measurements, columns=header)

    # Save the dataframe to a CSV file.
    if collected_measurements:
        output_file = output_directory / "reaction_wheel_measurements.csv"
        try:
            df.to_csv(output_file, index=False)
        except Exception as e:
            print(f"Error saving measurements to {output_file}: {e}")
        print(f"Successfully saved measurements to {output_file}")

    # TODO: Create a separate function that takes the measurements in CSV format
    # and generates plotly plots from them and writes those to disk as well.
    # Define this in a separate module.

    # TODO: Ideally, wrap all this up into a single installable package that you
    # can then just use via the command line.