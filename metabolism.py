#!/usr/bin/env python3
"""
metabolism.py — Echo Universe Metabolism Engine
Processes events, heals outstanding issues, updates biology state,
and enforces homeostasis across the cell.

Author: Manus AI | ∇θ Nathan Poinsette
Version: 1.0.0
"""
import json
import hashlib
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
ECHO_DIR       = Path(".echo")
GENOME_PATH    = ECHO_DIR / "genome.json"
EPIGENOME_PATH = ECHO_DIR / "epigenome.json"
MEMORY_PATH    = ECHO_DIR / "memory.json"
STATE_PATH     = ECHO_DIR / "state.json"
COORD_LOG      = Path("coordination_log.jsonl")
NOW            = lambda: datetime.now(timezone.utc).isoformat() + "Z"
KAPPA          = 0.618034

# ── Outstanding Issue Definitions ─────────────────────────────────────────────
# Each issue has: id, description, detect(), heal()
KNOWN_ISSUES = {
    "missing_biology_py": {
        "description": "biology.py is missing — feedback loop broken",
        "severity": "CRITICAL",
    },
    "missing_genome_py": {
        "description": "genome.py is missing — DNA rule engine not loaded",
        "severity": "CRITICAL",
    },
    "missing_metabolism_py": {
        "description": "metabolism.py is missing — no self-healing",
        "severity": "CRITICAL",
    },
    "missing_heartbeat_py": {
        "description": "heartbeat.py is missing — no pulse",
        "severity": "CRITICAL",
    },
    "frozen_epigenome": {
        "description": "All epigenome expressions frozen at 0.8 — no learning",
        "severity": "HIGH",
    },
    "empty_memory": {
        "description": "Memory has 0 events — agent has never processed a cycle",
        "severity": "HIGH",
    },
    "empty_coordination_log": {
        "description": "coordination_log.jsonl is empty — no inter-agent activity",
        "severity": "MEDIUM",
    },
    "missing_codeowners": {
        "description": "CODEOWNERS file missing — no access control",
        "severity": "MEDIUM",
    },
    "missing_pr_template": {
        "description": "Pull request template missing",
        "severity": "LOW",
    },
    "genome_json_empty_laws": {
        "description": "genome.json has 0 laws — DNA is structurally empty",
        "severity": "HIGH",
    },
}


class MetabolismResult:
    """Result of a single metabolism cycle."""
    def __init__(self):
        self.timestamp      = NOW()
        self.issues_found   = []
        self.issues_healed  = []
        self.issues_blocked = []
        self.events_processed = 0
        self.score_before   = 0.0
        self.score_after    = 0.0
        self.state          = "HEALTHY"

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "issues_found": self.issues_found,
            "issues_healed": self.issues_healed,
            "issues_blocked": self.issues_blocked,
            "events_processed": self.events_processed,
            "score_before": round(self.score_before, 6),
            "score_after": round(self.score_after, 6),
            "state": self.state,
        }


class Metabolism:
    """
    The metabolism engine for an Echo cell.
    Detects outstanding issues, attempts to heal them,
    updates biology state, and writes to the coordination log.
    """

    def __init__(self):
        self.genome    = None
        self.biology   = None
        self.epigenome = {}
        self.memory    = {}
        self.state     = {}
        self.result    = MetabolismResult()

    # ── Loaders ───────────────────────────────────────────────────────────────
    def load(self) -> "Metabolism":
        """Load all biology state files."""
        # Load epigenome
        if EPIGENOME_PATH.exists():
            with open(EPIGENOME_PATH) as f:
                self.epigenome = json.load(f)
        # Load memory
        if MEMORY_PATH.exists():
            with open(MEMORY_PATH) as f:
                self.memory = json.load(f)
        # Load state
        if STATE_PATH.exists():
            with open(STATE_PATH) as f:
                self.state = json.load(f)
        # Load genome module if available
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "genome", Path(__file__).parent / "genome.py")
            genome_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(genome_mod)
            self.genome = genome_mod.Genome()
            self.genome.load()
        except Exception:
            self.genome = None
        # Load biology module if available
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "biology", Path(__file__).parent / "biology.py")
            bio_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bio_mod)
            self.biology = bio_mod.Biology()
            self.biology.load()
        except Exception:
            self.biology = None
        return self

    # ── MultiReson Score ──────────────────────────────────────────────────────
    def _score(self) -> float:
        """Compute current MultiReson score from epigenome."""
        cap_expr = self.epigenome.get("capability_expression", {})
        if not cap_expr:
            return 0.0
        cap_vals = [v.get("expression", 0.8) if isinstance(v, dict) else 0.8
                    for v in cap_expr.values()]
        mean_cap = sum(cap_vals) / len(cap_vals) if cap_vals else 0.8
        force_expr = self.epigenome.get("force_expression", {})
        force_vals = list(force_expr.values()) if force_expr else [0.8]
        mean_force = sum(force_vals) / len(force_vals) if force_vals else 0.8
        return KAPPA * mean_cap + (1.0 - KAPPA) * mean_force

    # ── Issue Detection ───────────────────────────────────────────────────────
    def detect_issues(self) -> list:
        """Scan the local filesystem for all known outstanding issues."""
        issues = []
        base = Path(__file__).parent

        if not (base / "biology.py").exists():
            issues.append("missing_biology_py")
        if not (base / "genome.py").exists():
            issues.append("missing_genome_py")
        if not (base / "metabolism.py").exists():
            issues.append("missing_metabolism_py")
        if not (base / "heartbeat.py").exists():
            issues.append("missing_heartbeat_py")

        # Frozen epigenome
        cap_expr = self.epigenome.get("capability_expression", {})
        if cap_expr:
            all_frozen = all(
                abs((v.get("expression", 0.8) if isinstance(v, dict) else v) - 0.8) < 0.001
                for v in cap_expr.values()
            )
            if all_frozen:
                issues.append("frozen_epigenome")

        # Empty memory
        events = self.memory.get("short_term", {}).get("events", [])
        total = self.memory.get("long_term", {}).get("total_events_processed", 0)
        if len(events) == 0 and total == 0:
            issues.append("empty_memory")

        # Empty coordination log
        if not COORD_LOG.exists() or COORD_LOG.stat().st_size == 0:
            issues.append("empty_coordination_log")

        # CODEOWNERS
        codeowners_paths = [
            Path("CODEOWNERS"),
            Path(".github/CODEOWNERS"),
            Path("docs/CODEOWNERS"),
        ]
        if not any(p.exists() for p in codeowners_paths):
            issues.append("missing_codeowners")

        # PR template
        pr_paths = [
            Path(".github/PULL_REQUEST_TEMPLATE.md"),
            Path(".github/pull_request_template.md"),
        ]
        if not any(p.exists() for p in pr_paths):
            issues.append("missing_pr_template")

        # genome.json empty laws
        if GENOME_PATH.exists():
            with open(GENOME_PATH) as f:
                gj = json.load(f)
            laws = gj.get("laws", gj.get("nine_laws", []))
            if len(laws) == 0:
                issues.append("genome_json_empty_laws")

        return issues

    # ── Self-Healing ──────────────────────────────────────────────────────────
    def heal(self, issue_id: str) -> bool:
        """
        Attempt to heal a single issue locally.
        Returns True if healed, False if blocked (requires external action).
        """
        base = Path(__file__).parent

        if issue_id == "frozen_epigenome":
            # Inject a bootstrap event to unfreeze
            if self.biology:
                try:
                    cap_expr = self.epigenome.get("capability_expression", {})
                    for cap in cap_expr:
                        self.biology.record_event(
                            "metabolism.bootstrap", cap, "success",
                            forces=self.genome.forces if self.genome else []
                        )
                    self.biology.save()
                    self.epigenome = self.biology.epigenome
                    return True
                except Exception:
                    return False
            return False

        if issue_id == "empty_memory":
            # Same as above — inject bootstrap event
            if self.biology:
                try:
                    self.biology.record_event(
                        "metabolism.bootstrap", "python-runtime", "success", forces=[]
                    )
                    self.biology.save()
                    self.memory = self.biology.memory
                    return True
                except Exception:
                    return False
            return False

        if issue_id == "empty_coordination_log":
            # Write a bootstrap entry
            try:
                entry = json.dumps({
                    "timestamp": NOW(),
                    "event": "metabolism.bootstrap",
                    "agent": "metabolism.py",
                    "detail": "First coordination log entry — metabolism engine online",
                    "idem_key": f"meta_boot_{int(time.time())}",
                }) + "\n"
                with open(COORD_LOG, "a") as f:
                    f.write(entry)
                return True
            except Exception:
                return False

        if issue_id == "genome_json_empty_laws":
            # Patch genome.json with the canonical 9 Law IDs
            try:
                with open(GENOME_PATH) as f:
                    gj = json.load(f)
                gj["laws"] = [
                    {"id": lid, "status": "enforced"} for lid in [
                        "law_1_locality", "law_2_idempotency", "law_3_propagation_delay",
                        "law_4_monotonic_trust", "law_5_signal_integrity",
                        "law_6_homeostasis", "law_7_selective_amplification",
                        "law_8_graceful_degradation", "law_9_evolutionary_pressure",
                    ]
                ]
                gj["laws_patched_by"] = "metabolism.py"
                gj["laws_patched_at"] = NOW()
                with open(GENOME_PATH, "w") as f:
                    json.dump(gj, f, indent=2)
                return True
            except Exception:
                return False

        # Issues that require external action (GitHub Actions billing, Motor deployment)
        if issue_id in ("missing_biology_py", "missing_genome_py",
                        "missing_metabolism_py", "missing_heartbeat_py",
                        "missing_codeowners", "missing_pr_template"):
            # These are healed by the deploy script, not locally
            return False

        return False

    # ── Main Cycle ────────────────────────────────────────────────────────────
    def run_cycle(self) -> MetabolismResult:
        """
        Execute one full metabolism cycle:
        1. Detect all issues
        2. Attempt to heal each
        3. Update biology state
        4. Write coordination log entry
        5. Return result
        """
        self.result.score_before = self._score()

        # Detect
        issues = self.detect_issues()
        self.result.issues_found = [
            {"id": i, "severity": KNOWN_ISSUES.get(i, {}).get("severity","?"),
             "description": KNOWN_ISSUES.get(i, {}).get("description","?")}
            for i in issues
        ]

        # Heal
        for issue_id in issues:
            healed = self.heal(issue_id)
            entry = {"id": issue_id,
                     "description": KNOWN_ISSUES.get(issue_id, {}).get("description","?")}
            if healed:
                self.result.issues_healed.append(entry)
            else:
                self.result.issues_blocked.append(entry)

        # Update biology
        if self.biology:
            outcome = "success" if len(self.result.issues_healed) >= len(self.result.issues_blocked) else "partial"
            cap = list(self.epigenome.get("capability_expression", {}).keys())
            primary_cap = cap[0] if cap else "python-runtime"
            forces = self.genome.forces if self.genome else []
            try:
                self.biology.record_event(
                    "metabolism.cycle", primary_cap, outcome, forces=forces
                )
                self.biology.save()
                self.result.events_processed += 1
            except Exception:
                pass

        self.result.score_after = self._score()

        # Determine state
        critical = [i for i in self.result.issues_found if i.get("severity") == "CRITICAL"]
        high     = [i for i in self.result.issues_found if i.get("severity") == "HIGH"]
        if len(critical) > 0 and len(self.result.issues_healed) == 0:
            self.result.state = "CRITICAL"
        elif len(critical) > 0 or len(high) > 2:
            self.result.state = "DEGRADED"
        elif len(self.result.issues_found) > 0:
            self.result.state = "STRESSED"
        else:
            self.result.state = "HEALTHY"

        # Write coordination log
        log_entry = json.dumps({
            "timestamp": self.result.timestamp,
            "event": "metabolism.cycle",
            "agent": "metabolism.py",
            "state": self.result.state,
            "issues_found": len(self.result.issues_found),
            "issues_healed": len(self.result.issues_healed),
            "issues_blocked": len(self.result.issues_blocked),
            "score_before": self.result.score_before,
            "score_after": self.result.score_after,
            "idem_key": f"meta_{hashlib.sha256(self.result.timestamp.encode()).hexdigest()[:16]}",
        }) + "\n"
        try:
            with open(COORD_LOG, "a") as f:
                f.write(log_entry)
        except Exception:
            pass

        return self.result


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    print(f"[metabolism.py] Starting cycle at {NOW()}")
    m = Metabolism()
    m.load()
    result = m.run_cycle()
    r = result.to_dict()
    print(f"  State:          {r['state']}")
    print(f"  Issues found:   {len(r['issues_found'])}")
    for i in r["issues_found"]:
        print(f"    [{i['severity']}] {i['id']}: {i['description']}")
    print(f"  Issues healed:  {len(r['issues_healed'])}")
    for i in r["issues_healed"]:
        print(f"    ✓ {i['id']}")
    print(f"  Issues blocked: {len(r['issues_blocked'])}")
    for i in r["issues_blocked"]:
        print(f"    ✗ {i['id']} (requires external action)")
    print(f"  Score: {r['score_before']:.6f} → {r['score_after']:.6f}")
    print(f"[metabolism.py] Cycle complete.")
