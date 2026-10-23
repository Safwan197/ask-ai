import re
# Patterns that can destroy data or the system.
DANGEROUS_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*)",  # rm -r / rm -f / rm -rf
    r"\bmkfs\b",
    r"\bdd\s+.*of=",
    r">\s*/dev/sd",
    r":\(\)\s*\{.*\};\s*:",          
    # fork bomb
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\b.*\s/\s*$",
    r"\bshutdown\b|\breboot\b|\bhalt\b",
    r"\bsudo\b",
    r"(curl|wget)\s.*\|\s*(sudo\s+)?(ba|z)?sh",  # piping the internet into a shell
    r"\bgit\s+push\s+.*--force",
    r"\bdrop\s+(table|database)\b",
    r"\bformat\s+[a-zA-Z]:",
    r"\bdel\s+/[sS]\b",
]
def is_dangerous(command: str) -> bool:
    return any(re.search(p, command, re.IGNORECASE) for p in 
DANGEROUS_PATTERNS)