from os import pread, write, fstat

def _read(fd, offset):
    return pread(fd, 16, offset).lstrip(b'\x00')

def config(token=None, domain=None, ifname=None):
    if token and domain and ifname:
        write(1, bytes.fromhex(token).rjust(16, b'\x00'))
        write(1, domain.encode().rjust(16, b'\x00'))
        write(1, ifname.encode().rjust(16, b'\x00'))
        return None

    entries = []
    for offset in range(0, fstat(0).st_size, 48):
        token = _read(0, offset + 0).hex()
        domain = _read(0, offset + 16)
        ifname = _read(0, offset + 32)
        entries.append((domain, token, ifname))
    return entries
