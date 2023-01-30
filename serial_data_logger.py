"""

The Serial Data Logger allows the following:

1) Automatically finds the correct COM port and connects to Arduino.
2) Records the response from Arduino and make it available for processing functions
3) Can run in emulate mode, allowing the emulation of Arduino responses based on previously recorded files.
This option is useful and convenient for testing purposes, as it allows for testing of the end application without a permanent connection to the Arduino board.


All of these functions will be performed in a separate process, so as not to block the main application's processing.
"""

import time
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from typing import List

import serial

import serial_connection
from constants import _Const

CONST = _Const()


class SerialDataLogger():
    '''
        perform logging of data from serial port to file in separate process
    '''
    port: str = ""
    path: str = "."
    fseed: str = 'tmp'
    storage_file_name: str = ""
    speed: int = 0
    serial_speeds: List[int] = CONST.serial_speeds
    stdout_echo: bool = False
    reconnect: bool = False
    emulation_file = None
    emulation_delay = 0.01

    def __init__(self, port=None, speed=None, storage_path=None, filename_seed=None, stdout_echo=None, reconnect=None,
                        emulation_file=None, emulation_delay=0.01):
        """

        :param port: Port for connection, if not defined scan ports and try to select automatically
        :param speed: Speed of connection in bod
        :param storage_path: Path where files with logs should be stored
        :param filename_seed:
        :param stdout_echo: Should we perform echo output to stdout
        :param reconnect: Should we try to re-connect to board if lost connection
        :param emulation_file: If not empty emulation mode will use and emulation file will use as source of data
        :param emulation_delay: Emulated response delay for emulation mode in seconds
        """
        self.stdout_echo = stdout_echo
        self.reconnect = reconnect
        self.port = port

        if not speed:
            speed = 9600
        self.speed = speed

        if filename_seed:
            self.fseed = filename_seed
        self.storage_file_name = self._generate_storage_file_name(self.fseed)
        if storage_path:
            self.path = Path(storage_path)
        else:
            self.path = Path('.')

        if not self.path.is_dir():
            raise RuntimeError(f"Incorrect path to storage {str(self.path)}")

        if self.speed not in self.serial_speeds:
            raise RuntimeError(f"Incorrect serial speed {self.speed}")

        self.logging_queue = Queue()
        if not emulation_file is None:
            self.emulation_file = Path(emulation_file)
            if not self.emulation_file.exists():
                raise RuntimeError(f"Emulation file do not exists {self.emulation_file}")
            if not emulation_delay is None:
                self.emulation_delay = emulation_delay
            return

        if not self.port:
            ports = serial_connection.get_serial_ports_with_description()
            port_ard = [x for x, y in ports if y == 'Arduino Uno']
            if len(port_ard) == 0:
                raise RuntimeError(f"Can't find any available Arduino Port,specify one")
            self.port = port_ard[0]

    def _generate_storage_file_name(self, fseed: str) -> str:
        timestamp = datetime.today().strftime('%Y%m%d%H%M%S')
        return timestamp + "_" + fseed + ".txt"

    @property
    def file_name(self):
        """

        :return: Currently used file for store output from Arduino board
        """
        return self.storage_file_name

    def __log_output(self, fid, data, code=None):
        if self.stdout_echo:
            print(data)

        if code:
            try:
                data = data.decode(code)
            except (UnicodeDecodeError, AttributeError) as e:
                print(str(e))
                return False
        fid.write(data)
        return True

    def logging(self):
        fid = open(self.path.joinpath(self.storage_file_name), 'w')
        if self.emulation_file:
            self.__log_output(fid, "#---SerialDataLogger:Start emulated logging---\n")
        else:
            self.__log_output(fid, "#---SerialDataLogger:Start logging---\n")

        def serial_callback_fun(lstr):
            stop = False
            if not self.logging_queue.empty():
                msg = self.logging_queue.get()
                self.logging_queue.put(msg)
                if msg == 'stop':
                    stop = True
                    self.__log_output(fid, "#---SerialDataLogger:Finish logging---")
            if fid and not stop:
                self.__log_output(fid, lstr, 'utf-8')
                fid.flush()
                return True
            else:
                return False

        while True and self.emulation_file is None:
            try:
                serial_connection.process_one_line_of_serial_data(self.port, serial_callback_fun, self.speed)
                if not self.logging_queue.empty():
                    msg = self.logging_queue.get()
                    self.logging_queue.put(msg)
                    if msg == 'stop':
                        break
            except serial.SerialException as e:
                self.__log_output(fid, f"#---SerialDataLogger:Logging error:{str(e)}---")
                if not self.reconnect:
                    break
                else:
                    time.sleep(2)
                    timestamp = datetime.today().strftime('%Y%m%d%H%M%S')
                    self.__log_output(fid, f"#---SerialDataLogger:Attempt to re-connect time:{timestamp}---")

        if not self.emulation_file is None:
            ifid = open(self.emulation_file, 'r')
            while True:
                lstr = ifid.readline()
                time.sleep(self.emulation_delay)
                serial_callback_fun(lstr.encode('utf-8'))

    def start(self):
        self.proc = Process(target=self.logging)
        self.proc.start()

    def stop(self):
        print('stop')
        self.logging_queue.put('stop')


if __name__ == '__main__':
    sdl = SerialDataLogger(storage_path='../data', speed=115200, filename_seed='d001', stdout_echo=True, reconnect=True)
    print(sdl.file_name)
    sdl.logging()
