#!/usr/bin/env python
# Small utility to upload a file to an embedded Linux system that provides a shell
# via its serial port.

import serial
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
        self.s.open()

    def put(self, source, destination):
        data = open(source).read()
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
                dpart += '\\x%.2X' % int(ord(data[i]))
                j+=1
                i+=1

            self.write('\necho -ne "%s" >> %s\n' % (dpart, destination))

            # Show upload status
            if not self.quiet:
                print "%d / %d" % (i, data_size)

        return i

    def write(self, data):
        self.s.write(data)
        if data.endswith('\n'):
            # Have to give the target system time for disk/flash I/O
            time.sleep(self.IO_TIME)

    def close(self):
        self.s.close()





def usage():
    print '\nUsage: %s [OPTIONS]\n' % sys.argv[0]
    print '\t-s, --source=<local file>              Path to local file'
    print '\t-d, --destination=<remote file>        Path to remote file'
    print '\t-p, --port=<serial port>               Serial port to use [/dev/ttyUSB0]'
    print '\t-b, --baudrate=<baud>                  Serial port baud rate [115200]'
    print '\t-t, --time=<seconds>                   Time to wait between echo commands [0.1]'
    print '\t-q, --quiet                            Supress status messages'
    print '\t-h, --help                             Show help'
    print ''
    sys.exit(1)

def main():

    port = '/dev/ttyUSB0'
    baudrate = 115200
    source = None
    destination = None
    time = None
    quiet = False

    try:
        opts, args = GetOpt(sys.argv[1:],'p:b:s:d:t:qh', ['port=', 'baudrate=', 'source=', 'destination=', 'time=', 'quiet', 'help'])
    except GetoptError, e:
        print 'Usage error:', e
        usage()

    for opt, arg in opts:
        if opt in ('-p', '--port'):
            port = arg
        elif opt in ('-b', '--baudrate'):
            baudrate = arg
        elif opt in ('-s', '--source'):
            source = arg
        elif opt in ('-d', '--destination'):
            destination = arg
        elif opt in ('-t', '--time'):
            time = arg
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-h', '--help'):
            usage()

    if not source or not destination:
        print 'Usage error: must specify -s and -d options'
        usage()

    try:
        sftp = SerialFTP(port=port, baudrate=baudrate, time=time, quiet=quiet)
        size = sftp.put(source, destination)
        sftp.close()

        print 'Uploaded %d bytes from %s to %s' % (size, source, destination)
    except Exception, e:
        print "ERROR:", e


if __name__ == '__main__':
    main()
