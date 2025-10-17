#!/usr/bin/env python3
import re, sys
from pathlib import Path

ROOT = Path(".")
DEMO_PATTERNS = [
    r"\bdemo\b", r"\bseed(s)?\b", r"\bfixture(s)?\b", r"\bmock(s)?\b",
    r"\bsample(s)?\b", r"\bexample(s)?\b"
]
URL_REGEX = re.compile(r"https?://[A-Za-z0-9\.\-_:\/]+")

def is_text(p: Path) -> bool:
    try:
        txt = p.read_text(errors="ignore")
        return True
    except:
        return False

print("🔎 Scanning repository for demo data & hardcoded URLs...\n")

hits_demo = []
hits_url = []

for p in ROOT.rglob("*"):
    if p.is_dir(): 
        continue
    if p.suffix.lower() in [".png",".jpg",".jpeg",".gif",".webp",".pdf",".bin",".lock"]:
        continue
    try:
        txt = p.read_text(errors="ignore")
    except:
        continue
    # demo markers
    for pat in DEMO_PATTERNS:
        if re.search(pat, txt, flags=re.IGNORECASE):
            hits_demo.append(str(p))
            break
    # urls (frontend/src most important)
    if "ow-ai-dashboard/src" in str(p) or p.suffix.lower() in [".ts",".tsx",".js",".jsx",".py",".yml",".yaml",".json"]:
        if URL_REGEX.search(txt):
            hits_url.append(str(p))

def dedupe(lst): 
    return sorted(set(lst))

demo_files = dedupe(hits_demo)
url_files = dedupe(hits_url)

print("=== DEMO/SEED/MOCK/SAMPLE files (review):")
print("\n".join(demo_files) if demo_files else "✅ none found")

print("\n=== Files containing absolute URLs (review):")
print("\n".join(url_files) if url_files else "✅ none found")

print("\n📄 Next:")
print(" - Move any DEMO seed loaders behind an env flag (we’ll do this in step 4).")
print(" - Replace absolute URLs with env-driven VITE_API_URL (step 5).")
