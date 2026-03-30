# ReconX — OSINT Recon Tool

A modular OSINT CLI tool for domains, IPs and usernames.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Run all modules
python reconx.py example.com --all

# Individual modules
python reconx.py example.com --dns
python reconx.py example.com --whois
python reconx.py example.com --subdomains
python reconx.py example.com --geoip
python reconx.py johndoe --socials

# With JSON report
python reconx.py example.com --all --report
```

## Modules

| Flag | Description |
|------|-------------|
| `--dns` | DNS records (A, MX, NS, TXT, ...) |
| `--whois` | WHOIS registrar info |
| `--subdomains` | Subdomain enumeration via crt.sh |
| `--geoip` | IP geolocation |
| `--socials` | Username check on 8+ platforms |
| `--all` | Run all modules |
| `--report` | Save results as JSON |
