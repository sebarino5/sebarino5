#!/usr/bin/env python3
"""
ReconX - OSINT Recon Tool
"""

import argparse
import socket
import json
import sys
from datetime import datetime

import requests
import dns.resolver
import whois
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def banner():
    console.print(Panel.fit(
        "[bold red]ReconX[/bold red] [white]- OSINT Recon Tool[/white]\n"
        "[dim]by your portfolio project[/dim]",
        border_style="red"
    ))


# ── DNS ────────────────────────────────────────────────────────────────────────
def run_dns(target):
    console.print("\n[bold cyan][ DNS Records ][/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type", width=8)
    table.add_column("Value")

    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]
    found = False

    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(target, rtype)
            for r in answers:
                table.add_row(rtype, str(r))
                found = True
        except Exception:
            pass

    if found:
        console.print(table)
    else:
        console.print("[yellow]Keine DNS-Records gefunden.[/yellow]")


# ── WHOIS ──────────────────────────────────────────────────────────────────────
def run_whois(target):
    console.print("\n[bold cyan][ WHOIS ][/bold cyan]")
    try:
        w = whois.whois(target)
        fields = {
            "Registrar":      w.registrar,
            "Erstellt":       w.creation_date,
            "Läuft ab":       w.expiration_date,
            "Name Server":    w.name_servers,
            "Org":            w.org,
            "Land":           w.country,
        }
        table = Table(show_header=False)
        table.add_column("Feld", style="bold green", width=14)
        table.add_column("Wert")
        for k, v in fields.items():
            if v:
                val = ", ".join(v) if isinstance(v, list) else str(v)
                table.add_row(k, val[:120])
        console.print(table)
    except Exception as e:
        console.print(f"[red]WHOIS Fehler: {e}[/red]")


# ── SUBDOMAINS ─────────────────────────────────────────────────────────────────
def run_subdomains(target):
    console.print("\n[bold cyan][ Subdomains via crt.sh ][/bold cyan]")
    try:
        url = f"https://crt.sh/?q=%25.{target}&output=json"
        r = requests.get(url, timeout=15)
        data = r.json()
        subs = sorted({
            name.strip().lstrip("*.")
            for entry in data
            for name in entry.get("name_value", "").split("\n")
            if target in name
        })
        if subs:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", width=5)
            table.add_column("Subdomain")
            for i, sub in enumerate(subs, 1):
                table.add_row(str(i), sub)
            console.print(table)
            console.print(f"[green]{len(subs)} Subdomains gefunden.[/green]")
        else:
            console.print("[yellow]Keine Subdomains gefunden.[/yellow]")
    except Exception as e:
        console.print(f"[red]Subdomain-Fehler: {e}[/red]")


# ── GeoIP ──────────────────────────────────────────────────────────────────────
def run_geoip(target):
    console.print("\n[bold cyan][ GeoIP / IP-Info ][/bold cyan]")
    try:
        # IP auflösen falls Domain
        try:
            ip = socket.gethostbyname(target)
        except Exception:
            ip = target

        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        data = r.json()

        fields = {
            "IP":        data.get("ip"),
            "Stadt":     data.get("city"),
            "Region":    data.get("region"),
            "Land":      data.get("country_name"),
            "ISP":       data.get("org"),
            "Timezone":  data.get("timezone"),
            "Lat/Long":  f"{data.get('latitude')}, {data.get('longitude')}",
        }
        table = Table(show_header=False)
        table.add_column("Feld", style="bold green", width=12)
        table.add_column("Wert")
        for k, v in fields.items():
            if v:
                table.add_row(k, str(v))
        console.print(table)
    except Exception as e:
        console.print(f"[red]GeoIP Fehler: {e}[/red]")


# ── Username Check ─────────────────────────────────────────────────────────────
PLATFORMS = {
    "GitHub":    "https://github.com/{}",
    "Twitter":   "https://twitter.com/{}",
    "Instagram": "https://instagram.com/{}",
    "Reddit":    "https://reddit.com/user/{}",
    "TikTok":    "https://tiktok.com/@{}",
    "LinkedIn":  "https://linkedin.com/in/{}",
    "HackTheBox":"https://app.hackthebox.com/users/{}",
    "TryHackMe": "https://tryhackme.com/p/{}",
}

def run_socials(username):
    console.print(f"\n[bold cyan][ Username Check: {username} ][/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Plattform", width=14)
    table.add_column("Status", width=10)
    table.add_column("URL")

    for platform, url_template in PLATFORMS.items():
        url = url_template.format(username)
        try:
            r = requests.get(url, timeout=8, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                status = "[green]GEFUNDEN[/green]"
            elif r.status_code == 404:
                status = "[red]nicht da[/red]"
            else:
                status = f"[yellow]{r.status_code}[/yellow]"
        except Exception:
            status = "[dim]Timeout[/dim]"
        table.add_row(platform, status, url)

    console.print(table)


# ── Report ─────────────────────────────────────────────────────────────────────
def save_report(target, results: dict):
    filename = f"reconx_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    console.print(f"\n[bold green]Report gespeichert:[/bold green] {filename}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="reconx",
        description="ReconX - OSINT Recon Tool"
    )
    parser.add_argument("target", help="Domain, IP oder Username")
    parser.add_argument("--dns",        action="store_true", help="DNS Records")
    parser.add_argument("--whois",      action="store_true", help="WHOIS Lookup")
    parser.add_argument("--subdomains", action="store_true", help="Subdomain Enum")
    parser.add_argument("--geoip",      action="store_true", help="GeoIP Info")
    parser.add_argument("--socials",    action="store_true", help="Username Check")
    parser.add_argument("--all",        action="store_true", help="Alle Module")
    parser.add_argument("--report",     action="store_true", help="JSON Report speichern")

    args = parser.parse_args()
    banner()

    run_all = args.all or not any([
        args.dns, args.whois, args.subdomains, args.geoip, args.socials
    ])

    if args.dns or run_all:
        run_dns(args.target)
    if args.whois or run_all:
        run_whois(args.target)
    if args.subdomains or run_all:
        run_subdomains(args.target)
    if args.geoip or run_all:
        run_geoip(args.target)
    if args.socials or run_all:
        run_socials(args.target)

    if args.report:
        save_report(args.target, {"target": args.target, "timestamp": str(datetime.now())})

    console.print("\n[bold green]Scan abgeschlossen.[/bold green]")


if __name__ == "__main__":
    main()
