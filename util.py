from os import write

def printf(format, *args):
        write(2, format % args)
