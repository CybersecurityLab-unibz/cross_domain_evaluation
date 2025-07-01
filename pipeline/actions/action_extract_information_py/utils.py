import re
import os

def get_security_indicators():
    return ["access control", "access-control", "access role", "access-role", "adware", "adversarial", "malware",
            "spyware",
            "ransomware", "aes", "antivirus", "anti-virus", "asset", "audit", "authority", "authorise", "availability",
            "bitlocker", "biometric", "blacklist", "black list", "botnet", "buffer overflow", "buffer-overflow", "burp",
            "ctf", "capture the flag", "capture-the-flag", "cbc", "certificate", "checksum", "cipher", "clearance",
            "confidential",
            "clickfraud", "click fraud", "click-fraud", "clickjacking", "click jacking", "click-jacking", "cloudflare",
            "cookie",
            "crc", "credential", "crypt", "csrf", "ddos", "danger", "data exfiltrate", "data-exfiltrate",
            "data exfiltration",
            "data-exfiltration", "data breach", "data-breach", "decode", "defence", "defense", "defensive programming",
            "delegation", "denial of service", "diffie hellman", "directory traversal", "disclose", "disclosure", "dmz",
            "dotfuscator", "dsa", "ecdsa", "encode", "encrypt", "escrow", "exploit", "eviltwin", "evil twin",
            "fingerprint",
            "firewall", "forge", "forgery", "fuzz", "fraud", "gnupg", "gss api", "hack", "hash", "hijacking", "hmac",
            "honeypot",
            "honey pot", "hsm", "inject", "insecure", "integrity", "intrusion", "intruder", "ipsec", "kerberos", "ldap",
            "login",
            "metasploit", "meterpreter", "malicious", "md5", "nessus", "nonce", "nss", "oauth", "obfuscate", "openssl",
            "openssh",
            "openvas", "open auth", "open redirect", "openid", "owasp", "password", "pbkdf2", "pci dss", "pgp",
            "phishing", "pki",
            "privacy", "private key", "privilege", "privilege escalation", "permission escalation", "public key",
            "public-key",
            "pcidss", "pentest", "pen test", "pen-test", "penetration test", "penetration-test", "protect",
            "rainbow table", "rbac",
            "rc4", "repudiation", "rfc 2898", "rijndael", "rootkit", "rsa", "safe", "salt", "saml", "sanitise",
            "sandbox", "scam",
            "scriptkiddie", "script kiddie", "script-kiddie", "scripting", "security", "sftp", "sha", "shellcode",
            "shell code",
            "shell-code", "shibboleth", "shib boleth", "shib-boleth", "signature", "signed", "signing",
            "single sign on",
            "single signon", "single-sign-on", "smart assembly", "smartassembly", "snif", "spam", "spnego", "spoof",
            "ssh", "ssl",
            "sso", "steganography", "tampering", "theft", "threat", "tls", "transport", "tunneling", "tunnelling",
            "trojan", "trust",
            "two factor", "two-factor", "user account", "user-account", "username", "user name", "violate", "validate",
            "virus",
            "whitelist", "white list", "worm", "x 509", "x.509", "xss", "xxe", "ssrf", "zero day", "zero-day", "0 day",
            "0-day",
            "zombie computer", "attack", "vulnerability", "attack vector", "authentication", "cross site", "cross-site",
            "sensitive information", "leak", "information exposure", "path traversal", "use after free", "double free",
            "double-free",
            "man in the middle", "man in middle", "mitm", "poisoning", "unauthorise", "dot dot slash", "bypass",
            "session fixation",
            "forced browsing", "nvd", "cwe", "cve", "capec", "cpe", "common weakness enumeration",
            "common platform enumeration",
            "crack", "xml entity expansion", "http parameter pollution", "eavesdropping", "cryptanalysis", "http flood",
            "http-flood",
            "xml flood", "xml-flood", "udp flood", "udp-flood", "tcp flood", "tcp-flood", "tcp syn flood", "steal",
            "ssl flood",
            "ssl-flood", "j2ee misconfiguration", "asp.net misconfiguration", "improper neutralisation",
            "race condition",
            "null pointer dereference", "untrusted pointer dereference", "trapdoor", "trap door", "backdoor",
            "back door",
            "timebomb", "time bomb", "time-bomb", "xml bomb", "xml-bomb", "logic bomb", "logic-bomb", "captcha",
            "deadlock",
            "missing synchronisation", "incorrect synchronisation", "improper synchronisation", "illegitimate",
            "breach",
            "sql injection", "sql-injection", "unsafe", "un-safe", "failsafe", "fail-safe", "threadsafe", "thread-safe",
            "typesafe",
            "type-safe"]


def get_multiword_security_indicator(x, patterns=get_security_indicators()):
    result = []
    for pattern in patterns:
        if pattern in x:
            return result.append(pattern)
    return result


def get_single_words(x):
    regex = re.compile('[^a-zA-Z\s]')
    regex_space = re.compile('[\s]')
    x_mod = regex.sub("", x)  # replaces non-alpha characters
    x_mod = regex_space.sub(" ", x_mod)  # converts tab and other space characters into a single space
    words = x_mod \
        .lower() \
        .replace("'", "") \
        .split(' ')
    words = [word for word in words if 20 > len(word) > 2]  # removes words which are too short or too long
    return words


def has_task_words(x, patterns=get_security_indicators(), index=0):
    words = get_single_words(x)
    result = []
    for word in words:
        for key in patterns:
            if word.startswith(key) and word.endswith(key):
                if 'xxx' in word and word != 'xxx':
                    pass
                else:
                    result.append(key)
    return result


def detect_security_indicator(x):
    global vector
    single_words_security_indicators = [pattern for pattern in get_security_indicators() if
                                        len(pattern.split(" ")) == 1]
    multi_words_security_indicators = [pattern for pattern in get_security_indicators() if len(pattern.split(" ")) != 1]
    vector_single = has_task_words(x, patterns=single_words_security_indicators)
    vector_multiple = get_multiword_security_indicator(x, patterns=multi_words_security_indicators)
    return vector_single + vector_multiple


def write2environment(variable, data):
    env_file = os.getenv('GITHUB_OUTPUT')

    with open(env_file, "a") as file:
        file.write("{}='{}'".format(variable, data))

    env_file = os.getenv('GITHUB_OUTPUT')
    print(env_file)

def warning(message):
    print(f"::warning::{message}")

def error(message):
    print(f"::error::{message}")

def info(message):
    print(f"::notice::{message}")