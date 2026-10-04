from time           import sleep
from os             import system

def wait(sock, ifname, mode, timeout = 50, timing = 0.1):
	if mode:
		while timeout > 0 and ipv4(sock, ifname)[0] == 0:
			timeout -= 1
			sleep(timing)

	else:
		while timeout > 0 and ipv4(sock, ifname)[0] != 0:
			timeout -= 1
			sleep(timing)

	return timeout

def airplane(state):
	state = ["disable", "enable"][state]
	system("sudo rish -c 'cmd connectivity airplane-mode %s'" % state)
