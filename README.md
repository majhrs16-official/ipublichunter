# ipublichunter

Automated IP address management and dynamic DNS update tool for Linux systems.

## Overview

ipublichunter is a Python-based automation tool that monitors network interfaces and automatically updates dynamic DNS records when IP addresses change. It's designed for systems that need to maintain consistent domain name resolution despite changing public IP addresses.

## Architecture

```
src/ipublichunter/
├── __main__.py          # Entry point and main orchestration loop
├── config/
│   └── constants.py     # Netlink protocol constants and output formats
├── network/
│   └── netlink.py       # Low-level netlink socket communication
├── dns/
│   └── freemyip.py      # FreeMyIP.com DNS update client
├── android/
│   └── manager.py       # Android connectivity management (airplane mode)
├── utils/
│   └── output.py        # Formatted output utilities
└── exceptions.py        # Custom exception classes
```

## Components

### Network Layer (`network/netlink.py`)
Communicates directly with the Linux kernel via netlink sockets to:
- Query IPv4 addresses assigned to network interfaces
- Retrieve gateway information
- Monitor interface state changes

### DNS Client (`dns/freemyip.py`)
Handles communication with FreeMyIP.com dynamic DNS service:
- Updates DNS records with current IP address
- Manages configuration storage (token, domain, interface mappings)
- Supports both standard and verbose update modes

### Android Manager (`android/manager.py`)
Provides Android-specific connectivity control:
- Toggles airplane mode to force IP renewal
- Waits for interface state transitions with configurable timeouts

### Main Loop (`__main__.py`)
Orchestrates the automation workflow:
1. Detects when interface IP falls outside expected range (180-189.x.x.x)
2. Triggers airplane mode cycle to request new IP
3. Updates DNS records once valid IP is acquired
4. Continuously monitors with 1-second intervals

## Usage

```bash
# Install in development mode
pip install -e .

# Run with internet interface name
ipublichunter <interface_name>

# Configure DNS entries (token,domain,interface)
ipublichunter config <token>,<domain>,<interface>

# Manual update
ipublichunter update
```

## Requirements

- Linux kernel with netlink support
- Python 3.8+
- Root privileges (for netlink socket access)
- Android environment with `rish` (for airplane mode functionality)

## Configuration

The tool stores DNS configuration in stdin/stdout file descriptors:
- 16 bytes: token (hex encoded)
- 16 bytes: domain name
- 16 bytes: interface name

Multiple entries can be configured sequentially.

## Output Formats

Two formatted output modes:
- **CONFIG**: Standard status display with interface name and IP
- **FARM**: Extended display including connection timing metrics

## License

MIT License