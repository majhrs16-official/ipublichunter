# IPublicHunter

Automated public IP management and dynamic DNS update tool for Linux/Android systems.

## Overview

IPublicHunter monitors a network interface, keeps the public IP inside the expected range
(180-189.x.x.x in the current configuration), cycles Android airplane mode when the IP is
outside that range, and updates a FreeMyIP.com dynamic DNS record once a valid IP is
obtained. It also exposes a small UDP API for querying the current IPv4/gateway and for
requesting the next IP.

## Architecture

```
src/
└── ipublichunter/
    ├── __init__.py
    ├── main.py                # Monitor/update loop and API thread
    ├── remote.py              # UDP API client
    ├── config/
    │   ├── __init__.py
    │   ├── constants.py       # Netlink/API constants and output formats
    │   └── storage.py         # Fixed-size configuration records
    ├── network/
    │   ├── __init__.py
    │   ├── netlink.py         # Netlink socket communication
    │   └── api.py             # UDP API server
    ├── dns/
    │   ├── __init__.py
    │   └── freemyip.py        # FreeMyIP.com DNS update client
    ├── android/
    │   ├── __init__.py
    │   └── manager.py         # Airplane-mode control and wait helpers
    ├── utils/
    │   ├── __init__.py
    │   └── output.py          # Formatted output to stderr
    └── exceptions/
        ├── __init__.py
        └── RuntimeException.py
```

Imports are absolute from the package root, for example:

```python
from ipublichunter.network.netlink import ipv4
```

## Components

### Main loop (`main.py`)

1. Starts the UDP API in a daemon thread.
2. Publishes the current IP and updates DNS.
3. Detects when the interface IP is outside the expected range.
4. Cycles airplane mode (`airplane(True)` / `airplane(False)`) and waits for the interface
   to go down and come back up.
5. Repeats every second while the API has not requested shutdown.

The initial DNS update before validation is intentional. The loop updates DNS again after an
airplane-mode cycle. A valid-to-valid IP change that occurs without such a cycle is a known
edge case and may not be published immediately.

### Network layer (`network/netlink.py`)

Communicates with the Linux kernel through netlink sockets to:

- Query the IPv4 address assigned to an interface.
- Query the default gateway.
- Format an IPv4 value as text.

The `text` subcommand expects an **IP address**, not an interface name:

```bash
python -m ipublichunter.network.netlink text 1.2.3.4
```

### UDP API (`network/api.py`)

The API listens on `127.0.0.1:5002` by default and is intended for local control only. It is
started by `main.py`; `api.py` is a server library, not a standalone CLI.

Request (3 bytes):

| Byte | Field | Description |
|---:|---|---|
| 0 | magic | `0x12` |
| 1 | request id | Client-selected identifier, echoed in the response |
| 2 | command | `0=exit`, `1=get_ipv4`, `2=get_gateway`, `3=next_ipv4` |

Response:

| Field | Size | Description |
|---|---:|---|
| magic | 1 | `0x12` |
| request id | 1 | Echo of the request id |
| status | 1 | `1=success`, `0=error` |
| payload | 0 or 4 | IPv4 for `get_ipv4`/`get_gateway`; best-effort for `next_ipv4` |

`next_ipv4` is a best-effort control command: it enables airplane mode and waits for the
interface to lose its IPv4 address. The response may contain `0.0.0.0` or may never arrive,
because the interface changes while the request is being handled. A client timeout is
expected; `main.py` detects the invalid IP and performs the full recovery cycle.

Security warning: the API has **no authentication**. Keep it bound to loopback and never
expose port 5002 to untrusted networks. `exit` and `next_ipv4` are privileged operations.

### DNS client (`dns/freemyip.py`)

- Updates `freemyip.com` over HTTPS.
- Reads token/domain/interface records from `config/storage.py`.
- Retries up to 10 times and verifies the resolved DNS address before reporting success.
- The current implementation always requests a verbose response from FreeMyIP.

### Android manager (`android/manager.py`)

- `airplane(True)` enables airplane mode; `airplane(False)` disables it.
- Uses `rish -c 'cmd connectivity airplane-mode ...'` (Shizuku + rish, no `sudo`).
- `wait()` polls the interface until it goes down/up or the timeout budget is exhausted.

### Configuration storage (`config/storage.py`)

- Fixed-size records: 16 bytes token, 16 bytes domain, 16 bytes interface (48 bytes total).
- Multiple records can be concatenated.
- Reads use `fstat`/`pread`, so stdin must be a **regular file** (for example `< config.bin`).
  A shell pipe (`producer | ... update`) is not supported by the current code.
- Fields must not exceed 16 bytes. The current implementation does not truncate and can
  corrupt following records if a value is longer.

## Installation

```bash
pip install -e .
```

There is no separate console-script wrapper; run the package modules directly:

```bash
python -m ipublichunter.main wlan0
```

Requirements:

- Linux kernel with netlink support.
- Python 3.8+.
- Android environment with Shizuku + `rish` for airplane-mode control.
- No root required by the current code; `rish` runs the airplane-mode command.

## Usage

```bash
# Monitor and update DNS (also starts the UDP API)
python -m ipublichunter.main wlan0

# Write configuration records to a regular file
python -m ipublichunter.dns.freemyip config <token>,<domain>,<interface> > config.bin

# Read configuration from a regular file and update DNS
python -m ipublichunter.dns.freemyip update < config.bin

# Query netlink directly
python -m ipublichunter.network.netlink ipv4 wlan0
python -m ipublichunter.network.netlink gate wlan0
python -m ipublichunter.network.netlink text 1.2.3.4

# Query the UDP API (ipv4, gate, next, exit)
python -m ipublichunter.remote 127.0.0.1 5002 ipv4
```

The configuration file is binary; do not edit it as text. The current token field stores
the hex-decoded token and reads it back as hex, so tokens with leading zero bytes may lose
those bytes. This is a known limitation.

## Output formats

Two formatted output modes, written to stderr:

- **CONFIG**: status, interface name and IPv4 address.
- **FARM**: status, interface, IPv4, and two wait-budget values. The wait values are the
  remaining timeout budget (50 = transition detected immediately, 0 = timeout), not elapsed
  seconds.

## API example

```python
import socket

MAGIC = 0x12
request_id = 1
command = 1  # get_ipv4

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)
sock.sendto(bytes([MAGIC, request_id, command]), ("127.0.0.1", 5002))
data, _ = sock.recvfrom(16)
print(data.hex())
```

## License

GNU General Public License v3.0. See `LICENSE`.
