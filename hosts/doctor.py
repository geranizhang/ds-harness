#!/usr/bin/env python3
"""ds-harness doctor: is this machine's install healthy? Pointer dir, host verify, profile, tool health, knowledge-source
staleness, and both regression suites. Exit 1 on any FAIL."""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402

STALE_DAYS = 90


def main():
    ptr = c.POINTER_DIR
    hosts = (ptr / "hosts").read_text().split() if (ptr / "hosts").exists() else \
        ([(ptr / "host").read_text().strip()] if (ptr / "host").exists() else [])
    if not hosts:
        print(f"FAIL no install found ({ptr}/host missing); run bin/install.sh --host <host> --adapter <dir>")
        sys.exit(1)
    print(f"== hosts: {', '.join(hosts)}  adapter: {(ptr / 'adapter').read_text().strip()}")
    ok = True
    for host in hosts:
        print(f"-- verify {host}")
        r = subprocess.run([sys.executable, str(c.HERE / "verify.py"), host], text=True)
        ok &= r.returncode == 0
    cfg = c.load_adapter((ptr / "adapter").read_text().strip())
    src = c.hc.get(cfg, "knowledge.sources")
    if src:
        p = c.hc.path(cfg, src)
        if p.exists():
            today = dt.date.today()
            stale = []
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
                    continue
                cells = [x.strip() for x in line.strip("|").split("|")]
                m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", cells[-1]) if cells else None
                if m:
                    d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
                    if (today - d).days > STALE_DAYS:
                        stale.append((cells[0], d))
            print(f"== knowledge sources: {p} — {len(stale)} not checked in {STALE_DAYS} days")
            for name, d in stale:
                print(f"WARN source '{name}' last checked {d}")
        else:
            print(f"WARN knowledge.sources points to a missing file: {p}")
    else:
        print("INFO knowledge.sources not set (spec 0.3: a registry of the wiki / docs the handbooks were distilled from)")
    print("== evals")
    for cmd in ([sys.executable, str(c.CORE / "evals" / "run_validators.py")], ["bash", str(c.CORE / "evals" / "run_hook_tests.sh")]):
        r = subprocess.run(cmd, capture_output=True, text=True, env={**__import__("os").environ, "DS_HARNESS_ADAPTER_DIR": cfg["_dir"]})
        last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        ok &= r.returncode == 0
        print(("PASS " if r.returncode == 0 else "FAIL ") + f"{Path(cmd[-1]).name}: {last}")
    print("doctor:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
