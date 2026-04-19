#!/usr/bin/env python3
__NATHAN_POINSETTE__ = 'Nathan Poinsette | onlyecho822-source | ∇θ'
# ∇θ — Nathan Poinsette | Echo Universe | nabla-theta chain sealed truth preserved
"""
receptor.py — Echo Universe Cell Receptor
Enforces The 9 Laws. Manages state. Appends to ledger.

Source: Master Handoff Specification 2026-04-08
∇θ Operator — chain sealed, truth preserved
"""
from __future__ import annotations

import json
import os
import sys
import hashlib
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── PATHS ────────────────────────────────────────────────────────────────────

ECHO_DIR        = Path(".echo")
STATE_FILE      = ECHO_DIR / "state.json"
CAPABILITIES_F  = ECHO_DIR / "capabilities.yaml"
LEDGER_FILE     = Path("coordination_log.jsonl")
SCHEMA_FILE     = ECHO_DIR / "packet.schema.json"

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

MAX_IDEMPOTENCY_KEYS = 1000
IDEMPOTENCY_DECAY_HOURS = 168  # 7 days
ALLOWED_TRUST_LEVELS = {"internal", "external_verified", "external_unverified"}
CONTROL_TRUST_REQUIRED = "internal"

GENESIS_STATE = {
    "current": "IDLE",
    "idempotency_keys": [],
    "rejection_count": 0,
    "isolated": False,
    "stalled": False,
    "stalled_since": None,
    "last_reboot": None,
    "last_reboot_reason": None,
    "last_signal": None,
    "last_rejection": None,
    "schema_version": "1.0.0"
}

# ─── ERROR CODES ──────────────────────────────────────────────────────────────

class EchoError(Exception):
    def __init__(self, code: str, message: str, next_state: str):
        self.code = code
        self.message = message
        self.next_state = next_state
        super().__init__(message)

# ─── STATE MANAGEMENT ─────────────────────────────────────────────────────────

def load_state() -> dict:
    if not STATE_FILE.exists():
        return dict(GENESIS_STATE)
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        # Merge with genesis to handle new fields
        for k, v in GENESIS_STATE.items():
            if k not in state:
                state[k] = v
        return state
    except (json.JSONDecodeError, IOError) as e:
        print(f"[RECEPTOR] State load failed: {e} — triggering RESYNC")
        return dict(GENESIS_STATE)


def save_state(state: dict) -> None:
    ECHO_DIR.mkdir(exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_capabilities() -> list[str]:
    if not CAPABILITIES_F.exists():
        return []
    try:
        import yaml
        with open(CAPABILITIES_F) as f:
            caps = yaml.safe_load(f)
        return caps.get("receptor_classes", [])
    except Exception:
        return []

# ─── LEDGER ───────────────────────────────────────────────────────────────────

def ledger_append(entry: dict) -> None:
    """Append an entry to the immutable coordination ledger."""
    # Load last hash for chaining (Law 7: Causal Traceability)
    prev_hash = "genesis"
    if LEDGER_FILE.exists():
        try:
            lines = LEDGER_FILE.read_text().strip().splitlines()
            if lines:
                last = json.loads(lines[-1])
                prev_hash = last.get("entry_hash", "genesis")
        except Exception:
            pass

    entry["prev_hash"] = prev_hash
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    entry_str = json.dumps(entry, separators=(",", ":"))
    entry["entry_hash"] = hashlib.sha256(entry_str.encode()).hexdigest()

    with open(LEDGER_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ─── THE 9 LAWS ENFORCEMENT ───────────────────────────────────────────────────

def law_4_validate_expiry(signal: dict) -> None:
    """Law 4: State Half-Life — reject expired signals."""
    expires_at_str = signal.get("header", {}).get("expires_at")
    if not expires_at_str:
        raise EchoError("MISSING_EXPIRY", "expires_at required", "REJECTING")
    try:
        expires = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    except ValueError:
        raise EchoError("INVALID_EXPIRY", f"Cannot parse expires_at: {expires_at_str}", "REJECTING")
    if expires <= datetime.now(timezone.utc):
        raise EchoError("SIGNAL_EXPIRED", f"Signal expired at {expires_at_str}", "REJECTING")


def law_2_check_idempotency(signal: dict, state: dict) -> None:
    """Law 2: Idempotency — reject duplicate idempotency keys."""
    key = signal.get("payload", {}).get("idempotency_key")
    if not key:
        raise EchoError("MISSING_IDEMPOTENCY_KEY", "idempotency_key required", "REJECTING")
    existing = [e["key"] for e in state.get("idempotency_keys", [])]
    if key in existing:
        raise EchoError("DUPLICATE_SIGNAL", f"Idempotency key already processed: {key}", "REJECTING")


def law_6_validate_trust(signal: dict, state: dict) -> None:
    """Law 6: Identity Continuity — validate trust level."""
    trust = signal.get("auth", {}).get("trust_level")
    if trust not in ALLOWED_TRUST_LEVELS:
        raise EchoError("TRUST_VIOLATION", f"Unknown trust_level: {trust}", "ISOLATING")
    # CONTROL signals require internal trust
    intent = signal.get("payload", {}).get("intent", "")
    if intent == "CONTROL" and trust != CONTROL_TRUST_REQUIRED:
        raise EchoError("TRUST_VIOLATION", f"CONTROL signal requires internal trust, got: {trust}", "ISOLATING")
    # Check if cell is isolated
    if state.get("isolated") and intent != "CONTROL":
        raise EchoError("CELL_ISOLATED", "Cell is in ISOLATING state — only CONTROL/REBOOT accepted", "ISOLATING")


def law_8_check_attention(signal: dict, capabilities: list[str]) -> Optional[str]:
    """Law 8: Selective Attention — check receptor class. Returns None to drop."""
    receptor_class = signal.get("payload", {}).get("receptor_class", "")
    if not capabilities:
        return None  # No capabilities declared — accept all
    # Check exact match or prefix match (e.g., "analyzer.v1" matches "analyzer.*")
    for cap in capabilities:
        if cap == receptor_class or cap.endswith(".*") and receptor_class.startswith(cap[:-2]):
            return receptor_class
    return None  # Drop signal silently


def law_3_check_hops(signal: dict) -> None:
    """Law 3: Propagation Delay — enforce hop limits."""
    max_hops = signal.get("header", {}).get("max_hops", 0)
    hop_count = signal.get("header", {}).get("hop_count", 0)
    if hop_count > max_hops:
        raise EchoError("HOP_LIMIT_EXCEEDED", f"hop_count {hop_count} > max_hops {max_hops}", "REJECTING")


def law_1_check_locality(signal: dict) -> None:
    """Law 1: Locality — validate declared context (basic check)."""
    # Advanced: check declared_dependencies in capabilities.yaml
    # Basic: verify context field present if required
    pass  # Extend with specific context validation per repo

# ─── IDEMPOTENCY BUFFER MANAGEMENT ───────────────────────────────────────────

def add_idempotency_key(state: dict, key: str) -> dict:
    """Add key to buffer with timestamp. Evict old keys if over limit."""
    entries = state.get("idempotency_keys", [])
    entries.append({"key": key, "added_at": datetime.now(timezone.utc).isoformat()})
    # FIFO eviction
    if len(entries) > MAX_IDEMPOTENCY_KEYS:
        entries = entries[-MAX_IDEMPOTENCY_KEYS:]
    # Decay old entries
    cutoff = datetime.now(timezone.utc).timestamp() - (IDEMPOTENCY_DECAY_HOURS * 3600)
    entries = [
        e for e in entries
        if datetime.fromisoformat(e["added_at"].replace("Z", "+00:00")).timestamp() > cutoff
    ]
    state["idempotency_keys"] = entries
    return state

# ─── GIT OPERATIONS ───────────────────────────────────────────────────────────

def git_commit_state(trace_id: str, operation: str, receptor_class: str, root_trace_id: str) -> bool:
    """Commit state.json and ledger to git. Returns True on success."""
    try:
        subprocess.run(["git", "config", "user.email", "receptor@echo-universe.io"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Echo Receptor"], check=True, capture_output=True)
        subprocess.run(["git", "add", str(STATE_FILE), str(LEDGER_FILE)], check=True, capture_output=True)
        msg = (
            f"cell: processed signal {trace_id}\n\n"
            f"Operation: {operation}\n"
            f"Receptor: {receptor_class}\n"
            f"Root trace: {root_trace_id}\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"∇θ — law sealed, trace preserved"
        )
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True
        )
        if result.returncode == 0:
            print("[RECEPTOR] No changes to commit (already up to date)")
            return True
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[RECEPTOR] Git operation failed: {e}")
        return False

# ─── CONTROL SIGNAL HANDLERS ──────────────────────────────────────────────────

def handle_control_reboot(signal: dict, state: dict, reason: str = "manual") -> dict:
    """CONTROL/REBOOT — reset to genesis."""
    print(f"[RECEPTOR] CONTROL/REBOOT triggered: {reason}")
    # Preserve audit snapshot
    audit_file = ECHO_DIR / f"reboot_audit_{int(time.time())}.json"
    with open(audit_file, "w") as f:
        json.dump({"pre_reboot_state": state, "reason": reason}, f, indent=2)
    # Reset to genesis
    new_state = dict(GENESIS_STATE)
    new_state["last_reboot"] = datetime.now(timezone.utc).isoformat()
    new_state["last_reboot_reason"] = reason
    save_state(new_state)
    ledger_append({
        "event": "CONTROL_REBOOT",
        "reason": reason,
        "trace_id": signal.get("header", {}).get("trace_id", "manual"),
    })
    return new_state


def handle_control_resync(signal: dict) -> dict:
    """CONTROL/RESYNC — reconstruct state from ledger."""
    print("[RECEPTOR] CONTROL/RESYNC triggered — reconstructing from ledger")
    if not LEDGER_FILE.exists():
        print("[RECEPTOR] No ledger found — falling back to genesis")
        return dict(GENESIS_STATE)
    # Replay ledger entries
    keys_seen = []
    with open(LEDGER_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("event") == "signal_processed":
                    key = entry.get("idempotency_key")
                    if key:
                        keys_seen.append({"key": key, "added_at": entry.get("logged_at", "")})
            except json.JSONDecodeError:
                continue
    new_state = dict(GENESIS_STATE)
    new_state["idempotency_keys"] = keys_seen[-MAX_IDEMPOTENCY_KEYS:]
    save_state(new_state)
    ledger_append({"event": "CONTROL_RESYNC", "keys_reconstructed": len(keys_seen)})
    return new_state

# ─── MAIN RECEPTOR LOOP ───────────────────────────────────────────────────────

def process_signal(raw_payload: str) -> int:
    """
    Main receptor function. Returns exit code:
      0 = success (IDLE)
      1 = rejection (REJECTING)
      2 = trust violation (ISOLATING)
      3 = conflict/stall (CONFLICT_STALLED)
    """
    print("[RECEPTOR] Signal received — beginning processing")

    # Load state and capabilities
    state = load_state()
    capabilities = load_capabilities()

    # Parse signal
    try:
        signal = json.loads(raw_payload)
    except json.JSONDecodeError as e:
        print(f"[RECEPTOR] Parse failure: {e}")
        ledger_append({"event": "parse_failure", "error": str(e)})
        return 1

    trace_id = signal.get("header", {}).get("trace_id", "unknown")
    root_trace_id = signal.get("header", {}).get("root_trace_id", trace_id)
    operation = signal.get("payload", {}).get("operation", "UNKNOWN")
    receptor_class = signal.get("payload", {}).get("receptor_class", "")
    idempotency_key = signal.get("payload", {}).get("idempotency_key", "")
    intent = signal.get("payload", {}).get("intent", "")

    print(f"[RECEPTOR] trace_id={trace_id} operation={operation} receptor_class={receptor_class}")

    # ── CONTROL signal routing ─────────────────────────────────────────────
    if intent == "CONTROL":
        try:
            law_6_validate_trust(signal, state)
        except EchoError as e:
            print(f"[RECEPTOR] {e.code}: {e.message}")
            ledger_append({"event": "rejection", "code": e.code, "trace_id": trace_id})
            return 2

        if operation == "REBOOT":
            reason = signal.get("payload", {}).get("data", {}).get("reason", "manual")
            state = handle_control_reboot(signal, state, reason)
            git_commit_state(trace_id, "CONTROL_REBOOT", receptor_class, root_trace_id)
            print("[RECEPTOR] REBOOT complete — IDLE")
            return 0
        elif operation == "RESYNC":
            state = handle_control_resync(signal)
            git_commit_state(trace_id, "CONTROL_RESYNC", receptor_class, root_trace_id)
            print("[RECEPTOR] RESYNC complete — IDLE")
            return 0
        elif operation == "ISOLATE":
            state["isolated"] = True
            save_state(state)
            ledger_append({"event": "CONTROL_ISOLATE", "trace_id": trace_id})
            git_commit_state(trace_id, "CONTROL_ISOLATE", receptor_class, root_trace_id)
            print("[RECEPTOR] ISOLATE complete — ISOLATING")
            return 0

    # ── VALIDATION (The 9 Laws) ────────────────────────────────────────────
    state["current"] = "VALIDATING"

    try:
        law_4_validate_expiry(signal)
        law_2_check_idempotency(signal, state)
        law_6_validate_trust(signal, state)
        law_3_check_hops(signal)
        law_1_check_locality(signal)

        # Law 8: Selective Attention — check capabilities
        matched_class = law_8_check_attention(signal, capabilities)
        if capabilities and matched_class is None:
            print(f"[RECEPTOR] SELECTIVE_IGNORE: {receptor_class} not in capabilities — dropping")
            ledger_append({"event": "selective_ignore", "receptor_class": receptor_class, "trace_id": trace_id})
            state["current"] = "IDLE"
            save_state(state)
            return 0

    except EchoError as e:
        print(f"[RECEPTOR] {e.code}: {e.message} → {e.next_state}")
        state["current"] = e.next_state
        state["last_rejection"] = {"code": e.code, "trace_id": trace_id, "at": datetime.now(timezone.utc).isoformat()}
        if e.next_state == "ISOLATING":
            state["isolated"] = True
        if e.next_state == "REJECTING":
            state["rejection_count"] = state.get("rejection_count", 0) + 1
        save_state(state)
        ledger_append({"event": "rejection", "code": e.code, "message": e.message, "trace_id": trace_id, "next_state": e.next_state})
        return 1 if e.next_state == "REJECTING" else 2

    # ── SYNCHRONIZE MEMORY ─────────────────────────────────────────────────
    state["current"] = "SYNCHRONIZING_MEMORY"
    state = add_idempotency_key(state, idempotency_key)
    state["last_signal"] = {"trace_id": trace_id, "operation": operation, "at": datetime.now(timezone.utc).isoformat()}
    save_state(state)

    ledger_append({
        "event": "signal_processed",
        "trace_id": trace_id,
        "root_trace_id": root_trace_id,
        "operation": operation,
        "receptor_class": receptor_class,
        "idempotency_key": idempotency_key,
    })

    if not git_commit_state(trace_id, operation, receptor_class, root_trace_id):
        state["current"] = "CONFLICT_STALLED"
        state["stalled"] = True
        state["stalled_since"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        print("[RECEPTOR] CONFLICT_STALLED: git push failed")
        return 3

    # ── IDLE ───────────────────────────────────────────────────────────────
    state["current"] = "IDLE"
    state["stalled"] = False
    state["stalled_since"] = None
    state["rejection_count"] = 0
    save_state(state)
    print(f"[RECEPTOR] Signal processed successfully — IDLE | trace_id={trace_id}")
    return 0


if __name__ == "__main__":
    # Signal comes from GITHUB_EVENT_PATH environment variable
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        with open(event_path) as f:
            event = json.load(f)
        # Extract client_payload from repository_dispatch
        payload = event.get("client_payload", event)
        raw = json.dumps(payload)
    elif len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        print("[RECEPTOR] No signal provided")
        sys.exit(1)

    exit_code = process_signal(raw)
    sys.exit(exit_code)
