#!/usr/bin/env python3
"""
heartbeat.py — Echo Universe Heartbeat Monitor
The scheduled pulse of the organism. Runs on every push and on a cron schedule.
Calls genome.py (DNA), biology.py (learning), and metabolism.py (healing).
Writes a heartbeat record to coordination_log.jsonl.
Exits with code 0 (healthy) or 1 (critical) for GitHub Actions.

Author: Manus AI | ∇θ Nathan Poinsette
Version: 1.0.0
"""
import json
import sys
import os
import hashlib
import time
import importlib.util
from pathlib import Path
from datetime import datetime, timezone

# ── Constants ─────────────────────────────────────────────────────────────────
ECHO_DIR   = Path(".echo")
COORD_LOG  = Path("coordination_log.jsonl")
KAPPA      = 0.618034
NOW        = lambda: datetime.now(timezone.utc).isoformat() + "Z"
REPO       = os.environ.get("GITHUB_REPOSITORY", "unknown/unknown")
RUN_ID     = os.environ.get("GITHUB_RUN_ID", "local")
REF        = os.environ.get("GITHUB_REF_NAME", "local")
ACTOR      = os.environ.get("GITHUB_ACTOR", "heartbeat.py")
START_TIME = datetime.now(timezone.utc)


def load_module(name: str, path: Path):
    """Dynamically load a Python module from a file path."""
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"  [heartbeat] WARNING: Could not load {name}: {e}")
        return None


def idem_key(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def write_pulse(record: dict):
    """Append a heartbeat record to coordination_log.jsonl."""
    try:
        COORD_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(COORD_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"  [heartbeat] WARNING: Could not write pulse: {e}")


def print_banner(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"  Repo:   {REPO}")
    print(f"  Run:    {RUN_ID} | Ref: {REF}")
    print(f"  Time:   {NOW()}")
    print(f"{'='*65}")


# ── Main Heartbeat ─────────────────────────────────────────────────────────────
def main():
    print_banner("ECHO UNIVERSE HEARTBEAT v1.0.0")
    base = Path(__file__).parent
    os.chdir(base)

    pulse = {
        "timestamp": NOW(),
        "event": "heartbeat.pulse",
        "agent": "heartbeat.py",
        "repo": REPO,
        "run_id": RUN_ID,
        "ref": REF,
        "actor": ACTOR,
        "idem_key": idem_key(f"hb_{REPO}_{RUN_ID}_{START_TIME.isoformat()}"),
        "layers": {},
        "issues_found": [],
        "issues_healed": [],
        "issues_blocked": [],
        "score": None,
        "state": "UNKNOWN",
        "exit_code": 0,
    }

    # ── Layer 1: DNA (genome.py) ───────────────────────────────────────────────
    print("\n[1/3] DNA Layer — genome.py")
    genome_mod = load_module("genome", base / "genome.py")
    genome = None
    if genome_mod:
        try:
            genome = genome_mod.Genome()
            genome.load()
            summary = genome.summary()
            pulse["layers"]["genome"] = {
                "status": "LOADED",
                "kappa": summary["kappa"],
                "forces": summary["forces"],
                "capabilities": summary["capabilities"],
                "laws_count": len(summary["laws"]),
            }
            print(f"  ✓ Loaded | κ={summary['kappa']} | {len(summary['laws'])} laws | forces={summary['forces']}")
        except Exception as e:
            pulse["layers"]["genome"] = {"status": "ERROR", "error": str(e)}
            print(f"  ✗ Error: {e}")
    else:
        pulse["layers"]["genome"] = {"status": "MISSING"}
        print(f"  ✗ genome.py not found")
        pulse["issues_found"].append({"id": "missing_genome_py", "severity": "CRITICAL"})

    # ── Layer 2: Biology (biology.py) ─────────────────────────────────────────
    print("\n[2/3] Biology Layer — biology.py")
    bio_mod = load_module("biology", base / "biology.py")
    bio = None
    if bio_mod:
        try:
            bio = bio_mod.Biology()
            bio.load()
            forces = genome.forces if genome else []
            cap_expr = bio.epigenome.get("capability_expression", {})
            caps = list(cap_expr.keys())
            primary_cap = caps[0] if caps else "python-runtime"
            score_before = bio.multireson_score(primary_cap, forces)
            pulse["layers"]["biology"] = {
                "status": "LOADED",
                "score_before": round(score_before, 6),
                "capabilities": caps,
                "memory_events": len(bio.memory.get("short_term", {}).get("events", [])),
                "total_processed": bio.memory.get("long_term", {}).get("total_events_processed", 0),
            }
            print(f"  ✓ Loaded | score={score_before:.6f} | caps={caps} | memory_events={pulse['layers']['biology']['memory_events']}")
        except Exception as e:
            pulse["layers"]["biology"] = {"status": "ERROR", "error": str(e)}
            print(f"  ✗ Error: {e}")
            bio = None
    else:
        pulse["layers"]["biology"] = {"status": "MISSING"}
        print(f"  ✗ biology.py not found")
        pulse["issues_found"].append({"id": "missing_biology_py", "severity": "CRITICAL"})

    # ── Layer 3: Metabolism (metabolism.py) ───────────────────────────────────
    print("\n[3/3] Metabolism Layer — metabolism.py")
    meta_mod = load_module("metabolism", base / "metabolism.py")
    if meta_mod:
        try:
            meta = meta_mod.Metabolism()
            meta.load()
            result = meta.run_cycle()
            r = result.to_dict()
            pulse["layers"]["metabolism"] = {
                "status": "RAN",
                "state": r["state"],
                "issues_found": len(r["issues_found"]),
                "issues_healed": len(r["issues_healed"]),
                "issues_blocked": len(r["issues_blocked"]),
                "score_before": r["score_before"],
                "score_after": r["score_after"],
            }
            pulse["issues_found"].extend(r["issues_found"])
            pulse["issues_healed"].extend(r["issues_healed"])
            pulse["issues_blocked"].extend(r["issues_blocked"])
            print(f"  ✓ Ran | state={r['state']} | found={len(r['issues_found'])} | healed={len(r['issues_healed'])} | blocked={len(r['issues_blocked'])}")
            print(f"  ✓ Score: {r['score_before']:.6f} → {r['score_after']:.6f}")
        except Exception as e:
            pulse["layers"]["metabolism"] = {"status": "ERROR", "error": str(e)}
            print(f"  ✗ Error: {e}")
    else:
        pulse["layers"]["metabolism"] = {"status": "MISSING"}
        print(f"  ✗ metabolism.py not found")
        pulse["issues_found"].append({"id": "missing_metabolism_py", "severity": "CRITICAL"})

    # ── Record biology event for this heartbeat ────────────────────────────────
    if bio and genome:
        try:
            bio.record_event(
                "heartbeat.pulse",
                primary_cap,
                "success",
                forces=genome.forces,
            )
            bio.save()
            pulse["layers"]["biology"]["score_after"] = round(
                bio.multireson_score(primary_cap, genome.forces), 6
            )
            print(f"\n  ✓ Biology updated | score_after={pulse['layers']['biology']['score_after']:.6f}")
        except Exception as e:
            print(f"\n  ✗ Biology update failed: {e}")

    # ── Compute final score ────────────────────────────────────────────────────
    if "score_after" in pulse["layers"].get("metabolism", {}):
        pulse["score"] = pulse["layers"]["metabolism"]["score_after"]
    elif "score_before" in pulse["layers"].get("biology", {}):
        pulse["score"] = pulse["layers"]["biology"]["score_before"]
    else:
        pulse["score"] = 0.0

    # ── Determine overall state ────────────────────────────────────────────────
    critical = [i for i in pulse["issues_found"] if i.get("severity") == "CRITICAL"]
    if critical and not pulse["issues_healed"]:
        pulse["state"] = "CRITICAL"
        pulse["exit_code"] = 1
    elif critical:
        pulse["state"] = "DEGRADED"
        pulse["exit_code"] = 0  # healed — don't fail the workflow
    elif pulse["issues_found"]:
        pulse["state"] = "STRESSED"
        pulse["exit_code"] = 0
    else:
        pulse["state"] = "HEALTHY"
        pulse["exit_code"] = 0

    # ── Print summary ──────────────────────────────────────────────────────────
    elapsed = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    print(f"\n{'='*65}")
    print(f"  HEARTBEAT COMPLETE")
    print(f"  State:    {pulse['state']}")
    print(f"  Score:    {pulse['score']:.6f}")
    print(f"  Issues:   found={len(pulse['issues_found'])} | healed={len(pulse['issues_healed'])} | blocked={len(pulse['issues_blocked'])}")
    print(f"  Elapsed:  {elapsed:.2f}s")
    print(f"{'='*65}\n")

    if pulse["issues_blocked"]:
        print("BLOCKED ISSUES (require external action):")
        for i in pulse["issues_blocked"]:
            print(f"  ✗ {i['id']}: {i.get('description','?')}")
        print()

    # ── Write pulse to coordination log ───────────────────────────────────────
    write_pulse(pulse)

    # ── GitHub Actions output ──────────────────────────────────────────────────
    gha_output = os.environ.get("GITHUB_OUTPUT", "")
    if gha_output:
        with open(gha_output, "a") as f:
            f.write(f"heartbeat_state={pulse['state']}\n")
            f.write(f"heartbeat_score={pulse['score']:.6f}\n")
            f.write(f"issues_found={len(pulse['issues_found'])}\n")
            f.write(f"issues_healed={len(pulse['issues_healed'])}\n")
            f.write(f"issues_blocked={len(pulse['issues_blocked'])}\n")

    sys.exit(pulse["exit_code"])


if __name__ == "__main__":
    main()
