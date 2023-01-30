import glob
import sys

import serial
from serial.tools import list_ports


def get_serial_ports_crossplatform():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def get_serial_ports():
    """ Lists serial port names using PySerial
        :returns:
            A list of the serial ports available on the system
    """
    ports = serial.tools.list_ports.comports()
    portsname = [p.device for p in ports]
    return portsname


def get_serial_ports_with_description():
    """ Lists serial port names using PySerial
        :returns:
            A list of the serial ports available on the system
            And description of them
    """
    ports = list(serial.tools.list_ports.comports())
    result = []

    for port in ports:
        if not port.description.startswith("Arduino"):
            if port.manufacturer is not None:
                if port.manufacturer.startswith("Arduino") and \
                        port.device.endswith(port.description):
                    port.description = "Arduino Uno"
                else:
                    continue
            else:
                continue
        if port.device:
            port_names = port.device
            port_descr = str(port.description)
            result.append((port_names, port_descr))
    return result


def process_one_line_of_serial_data(port, callback_function, speed=9600, continue_when_fail=None):
    s = serial.Serial(port, speed, timeout=5)
    while True:
        input_line = s.readline()
        try:
            if not callback_function(input_line):
                break
        except Exception as e:
            if continue_when_fail:
                continue
            else:
                raise e


if __name__ == '__main__':
    def print_line(line):
        print(line)
        return True


    port_desc = get_serial_ports_with_description()
    ports_with_arduino_uno = [x for x, y in port_desc if y == 'Arduino Uno']
    process_one_line_of_serial_data(ports_with_arduino_uno[0], print_line)
