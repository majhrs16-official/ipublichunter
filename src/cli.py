#! /usr/bin/env python3
from os             import write
from sys            import argv
from time           import sleep

try:
    from .config.constants import CONFIG, FARM
    from .dns.freemyip import configAll, updateAll
    from .network.netlink import netlink, ipv4
    from .utils.output import printf
    from .android.manager import airplane, wait
except ImportError:
    from config.constants import CONFIG, FARM
    from dns.freemyip import configAll, updateAll
    from network.netlink import netlink, ipv4
    from utils.output import printf
    from android.manager import airplane, wait

def find(ifname):
	configurate = False

	with netlink() as sock:
		while (ip := ipv4(sock, ifname))[0] not in range(180, 190):
			airplane(True)
			down = wait(sock, ifname, False)

			airplane(False)
			up = wait(sock, ifname, True)

			printf(FARM,
				b"FAIL".center(6),
				ifname.encode(),
				*ip, down, up
			)

			configurate = True

	return configurate

def up(ifname_internet):
	with netlink() as sock:
		printf(CONFIG,
			b"OK".center(6),
			ifname_internet.encode(),
			*ipv4(sock, ifname_internet)
		)
	updateAll()

def main(path, ifname_internet):
	configurate = True

	while True:
		if configurate:
			up(ifname_internet)
		sleep(1)
		configurate = find(ifname_internet)
	return 0

if __name__ == "__main__":
	try:
		exit(main(*argv))

	except KeyboardInterrupt:
		exit(0)

	except TypeError as e:
		write(2, f"{e}\n".encode())
		exit(1)

	except Exception as e:
		write(2, f"{e.__class__.__name__}: {e}\n".encode())
		raise
