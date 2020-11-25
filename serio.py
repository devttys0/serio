#!/usr/bin/env python
# Small utility to upload a file to an embedded Linux system that provides a shell
# via its serial port.

import sys, time
from getopt import GetoptError, getopt as GetOpt

class SerialFTP:

    IO_TIME = .1
    BYTES_PER_LINE = 20

    def __init__(self, port=None, baudrate=None, time=None, quiet=None):
        self.quiet = quiet
        if time is not None:
            self.IO_TIME = time
        self.s = serial.Serial(port=port, baudrate=baudrate)
        #self.s.open()

    def put(self, source, destination):
        data = open(source, 'rb').read()
        data_size = len(data)
        i = 0
        j = 0

        # Create/zero the file
        self.write('\necho -ne > %s\n' % destination)

        # Loop through all the bytes in the source file and append them to
        # the destination file BYTES_PER_LINE bytes at a time
        while i < data_size:
            j = 0
            dpart = ''

            while j < self.BYTES_PER_LINE and i < data_size:
                dpart += '\\x%.2X' % (data[i])
                j+=1
                i+=1

            self.write('\necho -ne "%s" >> %s\n' % (dpart, destination))

            # Show upload status
            if not self.quiet:
                print("%d / %d" % (i, data_size))

        return i

    def write(self, data):
        self.s.write(data.encode())
        if data.endswith('\n'):
            # Have to give the target system time for disk/flash I/O
            time.sleep(self.IO_TIME)

    def close(self):
        self.s.close()


class TelnetFTP(SerialFTP):

    def __init__(self, host, port, login=None, passwd=None, time=None, quiet=None):
        self.quiet = quiet
        if time is not None:
            self.IO_TIME = time
        self.s = telnetlib.Telnet(host, port, timeout=10)
        # We're not interested in matching input, just interested
        # in consuming it, until it stops
        DONT_MATCH = b"\xff\xff\xff"
        if login:
            print(self.s.read_until(DONT_MATCH, 0.5))
            login += "\n"
            self.s.write(login.encode())
            print(self.s.read_until(DONT_MATCH, 0.5))
            passwd += "\n"
            self.s.write(passwd.encode())
        # Skip shell banner
        print(self.s.read_until(DONT_MATCH, self.IO_TIME))


def usage():
    print('\nUsage: %s [OPTIONS]\n' % sys.argv[0])
    print('\t-s, --source=<local file>              Path to local file')
    print('\t-d, --destination=<remote file>        Path to remote file')
    print('\t    --telnet=<host>                    Upload via telnet instead of serial')
    print('\t-p, --port=<port>                      Serial port to use [/dev/ttyUSB0] or telnet port [23]')
    print('\t-b, --baudrate=<baud>                  Serial port baud rate [115200]')
    print('\t-t, --time=<seconds>                   Time to wait between echo commands [0.1]')
    print('\t    --login=<username>                 Login name for telnet')
    print('\t    --pass=<passwd>                    Password for telnet')
    print('\t-q, --quiet                            Supress status messages')
    print('\t-h, --help                             Show help')
    print('')
    sys.exit(1)

def main():

    host = None
    port = None
    baudrate = 115200
    login = None
    passwd = None
    source = None
    destination = None
    time = None
    quiet = False

    try:
        opts, args = GetOpt(sys.argv[1:],'p:b:s:d:t:qh', ['port=', 'baudrate=',
            'source=', 'destination=', 'time=', 'quiet', 'help', 'telnet=', 'login=', 'pass='])
    except GetoptError as e:
        print('Usage error:', e)
        usage()

    for opt, arg in opts:
        if opt in ('--telnet',):
            host = arg
        elif opt in ('--login',):
            login = arg
        elif opt in ('--pass',):
            passwd = arg
        elif opt in ('-p', '--port'):
            port = arg
        elif opt in ('-b', '--baudrate'):
            baudrate = arg
        elif opt in ('-s', '--source'):
            source = arg
        elif opt in ('-d', '--destination'):
            destination = arg
        elif opt in ('-t', '--time'):
            time = float(arg)
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-h', '--help'):
            usage()

    if not source or not destination:
        print('Usage error: must specify -s and -d options')
        usage()

    try:
        if host:
            global telnetlib
            import telnetlib
            if not port:
                port = 23
            print(host, port, time, quiet)
            sftp = TelnetFTP(host=host, port=port, login=login, passwd=passwd, time=time, quiet=quiet)
        else:
            global serial
            import serial
            if not port:
                port = '/dev/ttyUSB0'
            sftp = SerialFTP(port=port, baudrate=baudrate, time=time, quiet=quiet)
        size = sftp.put(source, destination)
        sftp.close()

        print('Uploaded %d bytes from %s to %s' % (size, source, destination))
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    main()
