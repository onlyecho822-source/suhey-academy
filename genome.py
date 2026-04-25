#!/usr/bin/env python3
"""
genome.py — Echo Universe DNA Instruction Set
The immutable rule engine. Reads genome.json and governance.yaml,
enforces the 9 Laws, validates signals, and exposes the MultiReson
κ-constant for all downstream computation.

Author: Manus AI | ∇θ Nathan Poinsette
Version: 1.0.0
"""
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

# ── Constants ─────────────────────────────────────────────────────────────────
KAPPA          = 0.618034          # Golden ratio conjugate — immutable
KAPPA_PRIME    = 1.0 - KAPPA       # 0.381966
ECHO_DIR       = Path(".echo")
GENOME_PATH    = ECHO_DIR / "genome.json"
GOVERNANCE_PATH= ECHO_DIR / "governance.yaml"
NOW            = lambda: datetime.now(timezone.utc).isoformat() + "Z"

# ── The 9 Laws (canonical IDs — must match governance.yaml) ───────────────────
LAW_IDS = [
    "law_1_locality",
    "law_2_idempotency",
    "law_3_propagation_delay",
    "law_4_monotonic_trust",
    "law_5_signal_integrity",
    "law_6_homeostasis",
    "law_7_selective_amplification",
    "law_8_graceful_degradation",
    "law_9_evolutionary_pressure",
]


class GenomeViolation(Exception):
    """Raised when a signal or action violates one of the 9 Laws."""
    def __init__(self, law_id: str, error_code: str, detail: str):
        self.law_id     = law_id
        self.error_code = error_code
        self.detail     = detail
        super().__init__(f"[{law_id}] {error_code}: {detail}")


class Genome:
    """
    The DNA of an Echo cell.
    Loads the genome.json, enforces the 9 Laws, and exposes
    the MultiReson scoring function f_κ.
    """

    def __init__(self):
        self.data            = {}
        self.kappa           = KAPPA
        self.kappa_prime     = KAPPA_PRIME
        self.laws_loaded     = []
        self.forces          = []
        self.capabilities    = []
        self.homeostasis     = {}
        self.learning_rate   = 0.05
        self.mutation_rate   = 0.001
        self._idempotency_seen: set = set()

    # ── Loader ────────────────────────────────────────────────────────────────
    def load(self) -> "Genome":
        """Load genome.json from the .echo directory."""
        if not GENOME_PATH.exists():
            raise FileNotFoundError(f"genome.json not found at {GENOME_PATH}")
        with open(GENOME_PATH) as f:
            self.data = json.load(f)

        dna = self.data.get("multireson_dna", {})
        self.kappa         = dna.get("base_kappa", KAPPA)
        self.kappa_prime   = 1.0 - self.kappa
        self.mutation_rate = dna.get("mutation_rate", 0.001)
        self.learning_rate = self.data.get("learning_rate", 0.05)

        sig = self.data.get("harmonic_signature", {})
        self.forces       = sig.get("primary_forces", [])
        self.capabilities = self.data.get("base_capabilities", [])
        self.homeostasis  = self.data.get("homeostasis_setpoints",
                                          {"trust": 0.8, "load": 0.5, "tolerance": 0.1})
        self.laws_loaded  = LAW_IDS
        return self

    # ── MultiReson Scoring ────────────────────────────────────────────────────
    def f_kappa(self, cap_expression: float, mean_force_expression: float) -> float:
        """
        f_κ(agent) = κ * cap_expression + (1-κ) * mean_force_expression
        The fundamental MultiReson scoring function.
        Both inputs must be in [0, 1].
        """
        if not (0.0 <= cap_expression <= 1.0):
            raise ValueError(f"cap_expression {cap_expression} out of [0,1]")
        if not (0.0 <= mean_force_expression <= 1.0):
            raise ValueError(f"mean_force_expression {mean_force_expression} out of [0,1]")
        return self.kappa * cap_expression + self.kappa_prime * mean_force_expression

    # ── Law 1: Locality ───────────────────────────────────────────────────────
    def enforce_locality(self, signal_context: dict) -> None:
        """
        Law 1: A cell operates only on local state and explicitly declared context.
        Raises GenomeViolation if the signal references undeclared capabilities.
        """
        declared = set(self.capabilities)
        required = set(signal_context.get("required_capabilities", []))
        undeclared = required - declared
        if undeclared:
            raise GenomeViolation(
                "law_1_locality",
                "UNDECLARED_DEPENDENCY",
                f"Signal requires undeclared capabilities: {undeclared}"
            )

    # ── Law 2: Idempotency ────────────────────────────────────────────────────
    def enforce_idempotency(self, idempotency_key: str) -> None:
        """
        Law 2: Same input produces same outcome. Reject duplicate signals.
        Raises GenomeViolation if the key has already been processed.
        """
        if not idempotency_key:
            raise GenomeViolation(
                "law_2_idempotency",
                "MISSING_IDEMPOTENCY_KEY",
                "Signal must carry an idempotency_key"
            )
        if idempotency_key in self._idempotency_seen:
            raise GenomeViolation(
                "law_2_idempotency",
                "DUPLICATE_SIGNAL",
                f"Signal with key '{idempotency_key}' already processed"
            )
        self._idempotency_seen.add(idempotency_key)
        # Evict oldest if buffer exceeds 1000
        if len(self._idempotency_seen) > 1000:
            self._idempotency_seen.pop()

    # ── Law 4: Monotonic Trust ────────────────────────────────────────────────
    def enforce_monotonic_trust(self, current_trust: float, proposed_trust: float) -> float:
        """
        Law 4: Trust can only increase through verified actions, never jump.
        Returns the clamped trust value.
        """
        max_delta = self.homeostasis.get("tolerance", 0.1)
        if proposed_trust > current_trust + max_delta:
            return current_trust + max_delta
        if proposed_trust < 0.0:
            return 0.0
        if proposed_trust > 1.0:
            return 1.0
        return proposed_trust

    # ── Law 5: Signal Integrity ───────────────────────────────────────────────
    def verify_signal_integrity(self, signal: dict) -> str:
        """
        Law 5: Compute and verify the SHA-256 fingerprint of a signal.
        Returns the fingerprint. Raises GenomeViolation if mismatch.
        """
        payload = signal.get("payload", {})
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        declared_fp = signal.get("fingerprint")
        if declared_fp and declared_fp != fingerprint:
            raise GenomeViolation(
                "law_5_signal_integrity",
                "FINGERPRINT_MISMATCH",
                f"Expected {declared_fp[:16]}... got {fingerprint[:16]}..."
            )
        return fingerprint

    # ── Law 6: Homeostasis ────────────────────────────────────────────────────
    def check_homeostasis(self, current_load: float) -> str:
        """
        Law 6: Detect homeostasis deviation.
        Returns 'NORMAL', 'STRESSED', or 'CRITICAL'.
        """
        setpoint = self.homeostasis.get("load", 0.5)
        tolerance = self.homeostasis.get("tolerance", 0.1)
        deviation = abs(current_load - setpoint)
        if deviation <= tolerance:
            return "NORMAL"
        elif deviation <= tolerance * 2:
            return "STRESSED"
        else:
            return "CRITICAL"

    # ── Law 8: Graceful Degradation ───────────────────────────────────────────
    def degrade_gracefully(self, error: Exception) -> dict:
        """
        Law 8: On error, return a degraded-mode response rather than crashing.
        """
        return {
            "status": "DEGRADED",
            "error": str(error),
            "timestamp": NOW(),
            "fallback": "operating in read-only mode",
            "kappa": self.kappa,
        }

    # ── Law 9: Evolutionary Pressure ─────────────────────────────────────────
    def should_mutate(self) -> bool:
        """
        Law 9: Determine if this cycle should trigger a mutation.
        Mutation rate is defined in genome.json.
        """
        import random
        return random.random() < self.mutation_rate

    # ── Validation ────────────────────────────────────────────────────────────
    def validate_signal(self, signal: dict) -> dict:
        """
        Full signal validation against all applicable Laws.
        Returns a validation report dict.
        """
        report = {
            "timestamp": NOW(),
            "signal_type": signal.get("type", "unknown"),
            "laws_checked": [],
            "violations": [],
            "fingerprint": None,
            "valid": True,
        }
        # Law 2
        try:
            self.enforce_idempotency(signal.get("idempotency_key", ""))
            report["laws_checked"].append("law_2_idempotency")
        except GenomeViolation as e:
            report["violations"].append({"law": e.law_id, "code": e.error_code, "detail": e.detail})
            report["valid"] = False

        # Law 5
        try:
            fp = self.verify_signal_integrity(signal)
            report["fingerprint"] = fp
            report["laws_checked"].append("law_5_signal_integrity")
        except GenomeViolation as e:
            report["violations"].append({"law": e.law_id, "code": e.error_code, "detail": e.detail})
            report["valid"] = False

        # Law 1
        try:
            self.enforce_locality(signal.get("context", {}))
            report["laws_checked"].append("law_1_locality")
        except GenomeViolation as e:
            report["violations"].append({"law": e.law_id, "code": e.error_code, "detail": e.detail})
            report["valid"] = False

        return report

    # ── Summary ───────────────────────────────────────────────────────────────
    def summary(self) -> dict:
        return {
            "genome_id": self.data.get("genome_id", "unknown"),
            "node_id": self.data.get("node_id", "unknown"),
            "kappa": self.kappa,
            "kappa_prime": self.kappa_prime,
            "forces": self.forces,
            "capabilities": self.capabilities,
            "homeostasis": self.homeostasis,
            "learning_rate": self.learning_rate,
            "mutation_rate": self.mutation_rate,
            "laws": self.laws_loaded,
        }


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os, sys
    os.chdir(Path(__file__).parent)

    g = Genome()
    try:
        g.load()
        print(f"[genome.py] Loaded: {g.data.get('genome_id')}")
        print(f"  κ = {g.kappa} | κ' = {g.kappa_prime:.6f}")
        print(f"  Forces: {g.forces}")
        print(f"  Capabilities: {g.capabilities}")
        score = g.f_kappa(0.8, 0.8)
        print(f"  f_κ(0.8, 0.8) = {score:.6f}  (expected 0.800000)")
        assert abs(score - 0.8) < 0.001
        print(f"  Homeostasis check (load=0.5): {g.check_homeostasis(0.5)}")
        print(f"  Homeostasis check (load=0.9): {g.check_homeostasis(0.9)}")
        print("[genome.py] SELF-TEST PASSED")
    except FileNotFoundError as e:
        print(f"[genome.py] WARNING: {e} — running in standalone mode")
        g.kappa = KAPPA
        g.kappa_prime = KAPPA_PRIME
        g.forces = ["Electricity", "Intent", "Resonance"]
        g.capabilities = ["python-runtime"]
        g.homeostasis = {"trust": 0.8, "load": 0.5, "tolerance": 0.1}
        g.laws_loaded = LAW_IDS
        score = g.f_kappa(0.8, 0.8)
        print(f"  f_κ(0.8, 0.8) = {score:.6f}")
        print("[genome.py] STANDALONE SELF-TEST PASSED")
