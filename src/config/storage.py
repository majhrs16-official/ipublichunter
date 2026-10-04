from os import pread, write, fstat

ENTRY_SIZE = 48
TOKEN_OFFSET = 0
DOMAIN_OFFSET = 16
IFNAME_OFFSET = 32
FIELD_SIZE = 16


def _read_field(fd: int, offset: int) -> bytes:
    return pread(fd, FIELD_SIZE, offset).lstrip(b'\x00')


def write_entry(token: str, domain: str, ifname: str, fd: int = 1) -> None:
    write(fd, bytes.fromhex(token).rjust(FIELD_SIZE, b'\x00'))
    write(fd, domain.encode().rjust(FIELD_SIZE, b'\x00'))
    write(fd, ifname.encode().rjust(FIELD_SIZE, b'\x00'))


def read_entries(fd: int = 0) -> list[tuple[str, str, str]]:
    entries = []
    size = fstat(fd).st_size
    for offset in range(0, size, ENTRY_SIZE):
        token = _read_field(fd, offset + TOKEN_OFFSET).hex()
        domain = _read_field(fd, offset + DOMAIN_OFFSET).decode()
        ifname = _read_field(fd, offset + IFNAME_OFFSET).decode()
        entries.append((domain, token, ifname))
    return entries


def parse_entry(entry: str) -> tuple[str, str, str]:
    token, domain, ifname = entry.split(",")
    return token, domain, ifname


def config(token: str | None = None, domain: str | None = None, ifname: str | None = None, read_fd: int = 0, write_fd: int = 1) -> list[tuple[str, str, str]] | None:
    if token and domain and ifname:
        write_entry(token, domain, ifname, write_fd)
        return None
    return read_entries(read_fd)