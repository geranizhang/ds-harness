#!/usr/bin/env python3
"""Verify an install for one host: pointer dir, links, hook entry, declared tools' health checks. Exit 1 on any failure."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402


def main(host_name):
    host = c.load_host(host_name)
    ok = True

    def check(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + msg)

    ptr = c.POINTER_DIR / "adapter"
    check(ptr.exists(), f"pointer {ptr}")
    if not ptr.exists():
        sys.exit(1)
    adapter = Path(ptr.read_text().strip())
    cfg = c.load_adapter(adapter)
    check((c.POINTER_DIR / "host").read_text().strip() == host_name if (c.POINTER_DIR / "host").exists() else False, f"host pointer = {host_name}")
    man = c.manifest_path(host_name)
    links = [Path(l) for l in man.read_text().splitlines() if l.strip()] if man.exists() else []
    check(links, f"manifest {man} ({len(links)} entries)")
    for l in links:
        if not l.exists():
            check(False, f"missing: {l}")
    hp = c.expand(host["hooks"]["file"])
    if host["hooks"]["file"].endswith(".json"):
        d = json.loads(hp.read_text()) if hp.exists() else {}
        check(any("guard" in json.dumps(e) for e in d.get("hooks", {}).get(host["hooks"]["event"], [])), f"hook entry in {hp}")
    if host["hooks"].get("stdin") == "unknown":
        print(f"WARN hook stdin protocol unverified on {host_name}: {host['hooks'].get('note', '')}")
    print(f"INFO profile: {cfg.get('_profile') or 'none (optional; ~/.ds-harness/profile.json)'}")
    for t in c.tools(cfg):
        hc_cmd = t.get("health_check")
        if t.get("legacy") or not hc_cmd:
            print(f"INFO tool {t['name']}: no health_check declared")
            continue
        ex = c.resolve_exec(t)
        if not ex:
            check(False, f"tool {t['name']}: not found (candidates {t.get('candidates') or t.get('command')}); see {t.get('setup_doc') or 'platform.setup'}")
            continue
        argv = ex + list(hc_cmd) if isinstance(hc_cmd, list) else hc_cmd
        try:
            r = subprocess.run(argv, shell=isinstance(argv, str), capture_output=True, text=True, timeout=20,
                               env={**__import__("os").environ, **c.hc.tool_env(t)})
            check(r.returncode == 0, f"tool {t['name']}: {' '.join(argv) if isinstance(argv, list) else argv} (exit {r.returncode}) {(r.stdout or r.stderr).strip().splitlines()[-1][:80] if (r.stdout or r.stderr).strip() else ''}")
        except subprocess.TimeoutExpired:
            check(False, f"tool {t['name']}: health check timed out (20s)")
        if t.get("kind") == "mcp":
            tf = c.expand(host["tools"]["file"])
            txt = tf.read_text() if tf.exists() else ""
            check(re.search(rf"mcp_servers\.{re.escape(t['name'])}\]|\"{re.escape(t['name'])}\"\s*:", txt), f"tool {t['name']} registered in {tf}")
    print("verify:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1])
