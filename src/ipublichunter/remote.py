#! /usr/bin/env python3

from contextlib import closing
from socket     import socket, timeout, AF_INET, SOCK_DGRAM
from random     import randint
from sys        import argv

from ipublichunter.config.constants import MAGIC
from ipublichunter.network.netlink  import textip

def send(udp, addr, id, command):
	udp.sendto(MAGIC.to_bytes(1) + bytes([id, command]), addr)

def main(path, host, port, command):
	sock = None

	try:
		sock = socket(AF_INET, SOCK_DGRAM)
		sock.settimeout(5.0)

		addr = (host, int(port))

		id = randint(0, 255)

		if command == "exit":
			send(sock, addr, id, 0)

		elif command == "ipv4":
			send(sock, addr, id, 1)

		elif command == "gate":
			send(sock, addr, id, 2)

		elif command == "next":
			send(sock, addr, id, 3)
			
		else:
			print(f"Comando '{command}' desconocido.")
			return

		data, addr = sock.recvfrom(1024)
		if len(data) < 3:
			print("Tamanio de paquete recibido invalido.")
			return

		if data[0] != MAGIC:
			print("Paquete invalido.")
			return

		if data[1] != id:
			print("Paquete de origen desconocido.")
			return

		if data[2] == 0:
			print("Fallo en la operacion.")

		elif data[2] == 1:
			print("Exito en la operacion.")

		if len(data) > 3:
			ip = textip(data[3:7])
			print(f"IP: {ip}")

	except timeout:
		print("Tiempo de espera agotado.")

	finally:
		sock and sock.close()

if __name__ == "__main__":
	try:
		exit(main(*argv))

	except KeyboardInterrupt:
		exit(0)

	except TypeError as e:
		print(f"{e}")
		exit(1)

	except Exception as e:
		print(f"{e.__class__.__name__}: {e}")
		raise
