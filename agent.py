#!/usr/bin/env python3
# ∇θ -- Nathan Poinsette | Echo Universe
__NATHAN_POINSETTE__ = True
"""
Echo Universe Tentacle Agent — Kraken Protocol v1
==================================================
Lightweight signal emitter. Reads local .echo/identity.json.
Emits heartbeat + telemetry to the motor via GitHub repository_dispatch.
Logs all activity to coordination_log.jsonl (append-only ledger).

Architecture:
  BRAIN (echo-kraken-brain): full receptor, 9 Laws, FSM, recovery protocol
  MOTOR (echo-kraken-motor): leader election, suppression, immune system
  TENTACLES (this file, 182 repos): local sense + emit, remote decide

Attribution: Nathan Poinsette | onlyecho822-source | ∇θ
"""
from __future__ import annotations
import json, os, sys, time, hashlib, uuid, subprocess
from pathlib import Path
from datetime import datetime, timezone

ECHO_DIR     = Path(".echo")
IDENTITY_F   = ECHO_DIR / "identity.json"
STATE_F      = ECHO_DIR / "state.json"
LEDGER_F     = Path("coordination_log.jsonl")
PROFILE_F    = ECHO_DIR / "repo-profile.yml"

PROTOCOL_VERSION = "kraken.v1"
NOW = lambda: datetime.now(timezone.utc).isoformat()

def load_identity():
    """Load capability declaration. Fail loud if missing."""
    if not IDENTITY_F.exists():
        sys.stderr.write(f"[TENTACLE] FATAL: {IDENTITY_F} missing. Run identity seed.\n")
        sys.exit(1)
    return json.loads(IDENTITY_F.read_text())

def load_state():
    """Load state, merging existing file with defaults to prevent KeyError on new fields.

    Previously: if .echo/state.json existed (seeded by receptor.py with a different
    schema), this returned it directly, missing cycle_count/last_heartbeat/trust_score/
    failure_count - which run() then tried to increment, raising KeyError.
    Root cause of the tentacle Intelligent Autonomous Agent failure cascade.
    """
    defaults = {
        "current_state": "IDLE",
        "cycle_count": 0,
        "last_heartbeat": None,
        "trust_score": 1.0,
        "failure_count": 0,
    }
    if not STATE_F.exists():
        return defaults
    existing = json.loads(STATE_F.read_text())
    for k, v in defaults.items():
        existing.setdefault(k, v)
    return existing

def save_state(state):
    ECHO_DIR.mkdir(exist_ok=True)
    STATE_F.write_text(json.dumps(state, indent=2))

def append_ledger(event):
    """Append-only coordination log. One event per line (JSONL)."""
    with LEDGER_F.open("a") as f:
        f.write(json.dumps(event) + "\n")

def sense_local():
    """Lightweight local observation — what does this tentacle see?"""
    cwd = Path(".")
    observations = {
        "has_ci": (cwd / ".github/workflows").exists(),
        "python_files": len(list(cwd.rglob("*.py"))),
        "markdown_files": len(list(cwd.rglob("*.md"))),
        "recent_activity": None,
    }
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cI"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            observations["recent_activity"] = r.stdout.strip()
    except Exception:
        pass
    return observations

def emit_heartbeat(identity, state, observations):
    """
    Emit signal packet conforming to echo-kraken-brain/.echo/packet.schema.json.
    In Phase 1, this writes to ledger only. Phase 2 will POST to motor.
    """
    trace = str(uuid.uuid4())
    packet = {
        "header": {
            "root_trace_id": trace,
            "trace_id": trace,
            "parent_id": None,
            "timestamp": NOW(),
            "expires_at": NOW(),  # placeholder; motor will recompute
            "hop_count": 0,
            "max_hops": 3,
            "schema_version": "1.0.0",
        },
        "auth": {
            "trust_level": "internal",
            "verification_ref": f"github://{os.getenv('GITHUB_REPOSITORY','local')}",
            "source_node": identity["node_id"],
        },
        "payload": {
            "event_type": "heartbeat",
            "node_id": identity["node_id"],
            "tier": identity["tier"],
            "role": identity["role"],
            "capabilities": identity["capabilities"],
            "observations": observations,
            "state": state["current_state"],
            "cycle": state["cycle_count"],
            "trust": state.get("trust_score", 1.0),
        }
    }
    return packet

def generate_profile(identity, observations):
    """Legacy profile for compatibility with old mesh."""
    ECHO_DIR.mkdir(exist_ok=True)
    profile_lines = [
        f"# Tentacle Profile — auto-generated {NOW()}",
        f"node_id: {identity['node_id']}",
        f"tier: {identity['tier']}",
        f"role: {identity['role']}",
        f"capabilities: {identity['capabilities']}",
        f"has_ci: {observations['has_ci']}",
        f"python_files: {observations['python_files']}",
        f"protocol: {PROTOCOL_VERSION}",
    ]
    PROFILE_F.write_text("\n".join(profile_lines) + "\n")

def run():
    identity = load_identity()
    state = load_state()
    observations = sense_local()

    state["cycle_count"] += 1
    state["last_heartbeat"] = NOW()
    packet = emit_heartbeat(identity, state, observations)
    append_ledger(packet)
    generate_profile(identity, observations)

    save_state(state)

    print(f"[TENTACLE] {identity['node_id']} cycle={state['cycle_count']} tier={identity['tier']} trust={state['trust_score']:.3f}")

if __name__ == "__main__":
    run()
