#! /usr/bin/env python3
from socket         import socket, AF_INET, AF_NETLINK, SOCK_RAW, NETLINK_ROUTE, if_nametoindex, inet_ntoa
from struct         import pack, unpack_from
from os             import write

from ipublichunter.config.constants import *
from ipublichunter.exceptions import RuntimeException
from sys            import argv

# --- Library ---

def netlink():
	return socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE)

def query(sock, nl_type, payload):
	header = pack("IHHII", 16 + len(payload), nl_type, NLM_F_REQUEST | NLM_F_ROOT | NLM_F_MATCH, 1, 0)
	data   = bytearray()
	sock.settimeout(1.0)

	try:
		sock.send(header + payload)

		while (part := sock.recv(65535)):
			data.extend(part)

			pos  = 0
			while pos + 16 <= len(part):
				h_len, h_type, _, _, _ = unpack_from("IHHII", part, pos)

				if h_type == NLMSG_DONE:
					raise RuntimeException

				if h_len < 16:
					break

				pos += (h_len + 3) & ~3

	except RuntimeException:
		pass

	except Exception as e:
		print(f"{e.__class__.__name__}: {e}")

	return memoryview(data)

def ipv4(netlink, ifname):
#	ifaddrmsg: family(1), prefixlen(1), flags(1), scope(1), index(4)
	try:
		idx = if_nametoindex(ifname)

	except:
		return bytes(4)


	view = query(netlink, RTM_GETADDR, pack("BBBB I", AF_INET, 0, 0, 0, 0))
	pos  = 0
	while pos + 16 <= len(view):
		h_len, h_type, _, _, _ = unpack_from("IHHII", view, pos)

		ppos = int(pos)
		pos += (h_len + 3) & ~3
		if h_type != RTM_NEWADDR:
			continue

		if_idx = unpack_from("I", view, ppos + 20)[0]
		if if_idx != idx:
			continue

		attr_ptr = ppos + 24
		while attr_ptr < ppos + h_len:
			r_len, r_type = unpack_from("HH", view, attr_ptr)

			if r_type == IFA_ADDRESS:
				return byteip(inet_ntoa(view[attr_ptr+4:attr_ptr+r_len]))

			attr_ptr += (r_len + 3) & ~3

	return bytes(4)

def gate(netlink, ifname):
	try:
		idx = if_nametoindex(ifname)

	except:
		return bytes(4)

#	rtmsg: address_family(1), dst_len(1), src_len(1), tos(1), table(1), protocol(1), scope(1), type(1), flags(4)
	view = query(netlink, RTM_GETROUTE, pack("BBBBBBBB I", AF_INET, 0, 0, 0, 0, 0, 0, 0, 0))
	pos  = 0

	while pos + 16 <= len(view):
		h_len, h_type, _, _, _ = unpack_from("IHHII", view, pos)

		ppos = int(pos)
		pos += (h_len + 3) & ~3

		if h_type != RTM_NEWROUTE:
			continue

		attr_ptr = ppos + 28
		target   = False
		ip       = bytes(4)

		while attr_ptr < ppos + h_len:
			r_len, r_type = unpack_from("HH", view, attr_ptr)

			if r_type == RTA_GATEWAY:
				ip = inet_ntoa(view[attr_ptr+4:attr_ptr+r_len])

			elif r_type == RTA_OIF and unpack_from("I", view, attr_ptr+4)[0] == idx:
				target = True

			if target and ip:
				return byteip(ip)

			attr_ptr += (r_len + 3) & ~3

	return bytes(4)

# --- App ---

def byteip(ip):
        return bytes(int(oct) for oct in ip.split("."))

def textip(ip):
	return "%i.%i.%i.%i" % (*ip,)

def unknown(sock, ifname):
	return b'Unknown command.'

def main(path, function, ifname):
	with netlink() as sock:
		ip = {
			"text": lambda _, ip: textip(ip).encode(),
			"ipv4": ipv4,
			"gate": gate
		}.get(function, unknown)(sock, ifname)
		write(1, ip)

	return 0

if __name__ == "__main__":
	try:
		exit(main(*argv))

	except TypeError as e:
		print(e)
		exit(1)
