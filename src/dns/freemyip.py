#! /usr/bin/env python3
from socket           import gethostbyname, gaierror
from urllib.error     import URLError
from urllib.request   import urlopen
from time             import sleep

from config.constants import CONFIG
from config.storage   import config
from network.netlink  import netlink, ipv4, textip
from utils.output     import printf

from sys              import argv

# --- Library ---

# Deprecated code
#def update(token, domain, ip, verbose = False, timeout = 5):
#	try:
#		ip      = textip(ip)
#		verbose = '&verbose=yes' if verbose else ''
#		url     = f'http://freemyip.com/update?token={token}&domain={domain}.freemyip.com&myip={ip}{verbose}'
#
#		with urlopen(url, timeout = timeout) as response:
#			return response.read().strip()
#
#	except (URLError, TimeoutError) as e:
#		return "FAIL"

def update(token, domain, ip, verbose = False, timeout = 5):
	ip     = textip(ip)
	domain = domain.decode()
	url    = f"http://freemyip.com/update?token={token}&domain={domain}.freemyip.com&myip={ip}&verbose=yes"

	for retry in range(10):
		sleep(1)

		try:
			with urlopen(url, timeout = timeout) as response:
				result = response.read().strip()

			dns = gethostbyname(f"{domain}.freemyip.com")
			write(3, f"{dns}\n".encode())

			if dns != ip:
				continue

			if verbose:
				return result

			elif b"OK" in result:
				return b"OK"

			elif b"FAIL" in result:
				return b"FAIL"

			else:
				continue

		except (URLError, TimeoutError, gaierror):
			continue

	return b"FAIL"

# --- App ---

def updateAll():
	with netlink() as sock:
		for host, id, ifname in config():
			ip   = ipv4(sock, ifname)
			text = update(id, host, ip)
			printf(CONFIG, text.center(6), host, *ip)

def configAll(*entries):
	for entry in entries:
		token, domain, ifname = entry.split(",")
		config(token, domain, ifname)

def unknown(*_):
	write(1, b"Unknown command.")

def main(path, mode, *config):
	{
		"config": configAll,
		"update": updateAll
	}.get(mode, unknown)(*config)
	return 0

if __name__ == '__main__':
	try:
		exit(main(*argv))

	except TypeError as e:
		print(e)
		raise
		exit(1)
