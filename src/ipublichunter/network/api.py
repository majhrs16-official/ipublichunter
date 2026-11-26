from contextlib import closing
from socket     import socket, AF_INET, SOCK_DGRAM
from time       import sleep

from ipublichunter.android.manager  import airplane, wait
from ipublichunter.config.constants import REMOTE, MAGIC, COMMANDS
from ipublichunter.network.netlink  import netlink, ipv4, gate
from ipublichunter.utils.output     import printf

def send(udp, addr, id, status, payload=b""):
    udp.sendto(MAGIC.to_bytes(1) + bytes([id, status]) + payload, addr)

def serve(ifname_internet, host = "127.0.0.1", port = 5002, stop = None):
	running = True
	with closing(socket(AF_INET, SOCK_DGRAM)) as sock:
		sock.bind((host, port))

		while running:
			try:
				try: data, addr = sock.recvfrom(1024)
				except OSError: continue

				if len(data) < 3:
					send(sock, addr, data[1] if len(data) > 1 else 0, 0)
					continue

				magic      = data[0]
				id         = data[1]
				command    = data[2]

				if magic != MAGIC:
					send(sock, addr, id, 0)
					continue

				if command >= len(COMMANDS):
					send(sock, addr, id, 0)
					continue

				printf(REMOTE, addr[0].encode(), addr[1], COMMANDS[command])

				if command == 0:
					send(sock, addr, id, 1)
					if stop is not None:
						stop()
					running = False

				elif command == 1:
					with netlink() as nl:
						send(sock, addr, id, 1, ipv4(nl, ifname_internet))

				elif command == 2:
					with netlink() as nl:
						send(sock, addr, id, 1, gate(nl, ifname_internet))

				elif command == 3:
					airplane(True) # Main.py detects the invalid IP and farm next IP.
					with netlink() as nl:
						wait(nl, ifname_internet, False)
						send(sock, addr, id, 1, ipv4(nl, ifname_internet))

			except Exception as exc:
				sleep(1)
