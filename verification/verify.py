# -*- coding: utf-8 -*-
"""One-command verification for the anonymous K3 case-study artifact.

This deliberately omits checks tied to the non-anonymous K3 paper itself.
It retains the evidence regimes discussed in the submission: five replayed
certificates, one recomputed certificate, and three frozen hour-scale
certificates checked by SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
CERTS = ROOT / "certificates"
PRODUCERS = Path(__file__).resolve().parent / "producers"
MPMATH_PIN = "1.3.0"
SYMPY_PIN = "1.14.0"

# Exact expected outcomes. Equality is intentional: an earlier verifier
# checked only prefixes, allowing contradictory suffixes to pass.
REPLAY = [
    ("open_chart_theorem", "open_chart_theorem.py",
     "uniform_open_chart_theorem_certified"),
    ("quantitative_atlas", "quantitative_atlas.py",
     "t2_fixed_k3_closed_quantitative_existence_level"),
    ("glue_obligations", "glue_obligations.py",
     "atlas_paper_glue_obligations_typed_and_transition_generators_derived_word_length_le_4"),
    ("smoothness_and_transitions", "smoothness_and_transitions.py",
     "atlas_paper_three_nonzero_lemma_carries_smoothness_and_coverage_pivot_degree3_invariant_transitions_explicit"),
    ("sigma_floor_correction", "sigma_floor_correction.py",
     "u1_sigma_floor_defect_confirmed_with_witness_radius_corrected_9p6e10_to_2p1e12_theorem_survives"),
]

RECOMPUTE = [
    ("atlas_coverage", "atlas_coverage.py",
     ["0.6", "4", "1e-3", "1000"],
     ("verdict", "tau", "w_min", "minor_floor_8tau", "total_boxes",
      "per_gauge", "statement", "domain", "arithmetic", "mu")),
]

HASHED = [
    ("bridge_atlas_panel",
     "58c06da48412c8b1dca175f7f7b44156b590d7f71be80b4831cdd4f4f1c5081c"),
    ("bridge_metric_path",
     "397c19b105819f79f93016fda4045e35b969375d8bfc2d880534c8096cc076be"),
    ("face_traversal_leaf",
     "9088e59844c7e0dd398cd5daa66ce11a1ddece7d4aca8fe8c07b47d08b9ae5c1"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_environment():
    try:
        import mpmath
        import numpy  # noqa: F401
        import sympy
    except ImportError as exc:
        return f"missing dependency: {exc.name}"
    if mpmath.__version__ != MPMATH_PIN:
        return f"mpmath {mpmath.__version__} installed; required {MPMATH_PIN}"
    if sympy.__version__ != SYMPY_PIN:
        return f"sympy {sympy.__version__} installed; required {SYMPY_PIN}"
    return None


def inspect_certificate(path: Path, expected_outcome: str):
    d = json.loads(path.read_text(encoding="utf-8"))
    passed, total = d.get("checks_passed"), d.get("checks_total")
    tests = d.get("perturbation_tests", {})
    field = "outcome" if "outcome" in d else "issue"
    ok = (passed is not None and passed == total and total > 0
          and all(bool(v) for v in tests.values())
          and str(d.get(field, "")) == expected_outcome)
    detail = f"checks {passed}/{total}"
    if tests:
        detail += f" · perturbations {sum(bool(v) for v in tests.values())}/{len(tests)}"
    return ok, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip replay and recomputation; check frozen hashes only")
    args = ap.parse_args()

    problem = check_environment()
    if problem:
        print(f"ENVIRONMENT: {problem}")
        print("VERDICT: FAIL")
        return 2

    failures = []
    lines = []

    if not args.quick:
        snapshot = {}
        for cert in ([c for c, _, _ in REPLAY]
                     + [c for c, _, _, _ in RECOMPUTE]):
            p = CERTS / f"{cert}.json"
            if p.exists():
                snapshot[p] = p.read_bytes()
        try:
            for cert, producer, outcome in REPLAY:
                p = CERTS / f"{cert}.json"
                sp = PRODUCERS / producer
                if not p.exists() or not sp.exists():
                    failures.append(cert)
                    lines.append(f"FAIL     {cert} [replay: missing input]")
                    continue
                # Check the bytes the reviewer actually received before
                # regeneration; replay alone once allowed a red shipped
                # certificate to hide behind a green regenerated one.
                shipped_ok, _ = inspect_certificate(p, outcome)
                r = subprocess.run([sys.executable, str(sp)], cwd=str(ROOT),
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    failures.append(cert)
                    lines.append(f"FAIL     {cert} [replay exit {r.returncode}]")
                    continue
                regenerated_ok, detail = inspect_certificate(p, outcome)
                ok = shipped_ok and regenerated_ok
                lines.append(f"{'PASS' if ok else 'FAIL'}     {cert} [replay] {detail}")
                if not ok:
                    failures.append(cert)

            for cert, producer, argv, fields in RECOMPUTE:
                p = CERTS / f"{cert}.json"
                sp = PRODUCERS / producer
                if not p.exists() or not sp.exists():
                    failures.append(cert)
                    lines.append(f"FAIL     {cert} [recompute: missing input]")
                    continue
                shipped = json.loads(snapshot[p].decode("utf-8"))
                r = subprocess.run([sys.executable, str(sp), *argv], cwd=str(ROOT),
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    failures.append(cert)
                    lines.append(f"FAIL     {cert} [recompute exit {r.returncode}]")
                    continue
                got = json.loads(p.read_text(encoding="utf-8"))
                # A prior implementation ran the expensive producer but
                # compared the shipped file with itself. Require evidence
                # that this exact target was rewritten before accepting an
                # empty diff.
                rewritten = got.get("seconds") != shipped.get("seconds")
                diff = [f for f in fields if got.get(f) != shipped.get(f)]
                ok = rewritten and not diff and got.get("verdict") == "CERTIFIED"
                lines.append(
                    f"{'PASS' if ok else 'FAIL'}     {cert} [recompute] "
                    + (f"{len(fields)} fields identical; {got.get('total_boxes')} boxes"
                       if ok else f"rewritten={rewritten}; differing={diff}"))
                if not ok:
                    failures.append(cert)
        finally:
            for p, blob in snapshot.items():
                p.write_bytes(blob)
    else:
        lines.append("(replay and recomputation skipped: --quick)")

    for cert, expected in HASHED:
        p = CERTS / f"{cert}.json"
        if not p.exists():
            failures.append(cert)
            lines.append(f"FAIL     {cert} [hash: missing]")
            continue
        got = sha(p)
        ok = got == expected
        lines.append(f"{'PASS' if ok else 'FAIL'}     {cert} [hash] {got[:16]}…")
        if not ok:
            failures.append(cert)

    print("Anonymous K3 verification artifact")
    print("\n".join(lines))
    if failures:
        print(f"VERDICT: FAIL — {', '.join(failures)}")
        return 1
    n = 0 if args.quick else len(REPLAY)
    m = 0 if args.quick else len(RECOMPUTE)
    print(f"VERDICT: PASS — {n} replayed, {m} recomputed, {len(HASHED)} hashed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
