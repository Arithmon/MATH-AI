# Anonymous K3 verification artifact

This repository is the minimal executable artifact accompanying a double-blind case study on failure-driven verification in human–AI mathematics.

The mathematical test object is an explicit K3 surface: the complete intersection of three diagonal quadrics in `P^5` with parameters `(1, 2, 3, 5, 7, 11)`. The submission studies the verification workflow rather than claiming that this artifact constitutes an independent peer review of the underlying K3 theorem.

## What is included

- `certificates/`: nine quantitative artifacts used by the case study.
- `verification/producers/`: the producers required for the five replayed certificates and the one recomputed coverage certificate, plus their shared surface model.
- `verification/verify.py`: a one-command verifier specialized to this anonymous review bundle.

The three hour-scale certificates are included as frozen artifacts and checked by SHA-256. Their full producing closures are deliberately not included in this minimal review bundle: reproducing them requires a substantially larger computational workspace and is not part of the one-command review path.

No paper source, author metadata, DOI, project URL, or original K3 repository history is included.

## Run

```bash
python -m pip install -r requirements.txt
python verification/verify.py
```

A full run has three evidence regimes:

1. **Replay** — five inexpensive certificates are regenerated. Every check and perturbation test must pass, the semantic outcome must equal its complete expected value, and the shipped certificate is checked independently of regenerated output.
2. **Recompute** — the coverage enumeration is rerun over `71,807,792` boxes and ten deterministic fields are compared with the shipped certificate. The verifier also requires evidence that recomputation rewrote the exact file being compared.
3. **Hash** — three hour-scale artifacts are checked against frozen SHA-256 values.

For a fast integrity check only:

```bash
python verification/verify.py --quick
```

## Why perturbations are present

The producers include targeted perturbation tests: coefficients, signs, bounds, or related assumptions are deliberately changed and the corresponding check is required to fail. These are regression tests for specific failure modes, not a substitute for formal proof or expert mathematical peer review.

## Scope

This artifact supports the methodological claims of the accompanying submission: in particular, that apparently green computations can survive while the mathematical statement, encoded specification, shipped artifact, or verifier is wrong. It does not claim autonomous mathematical discovery, model independence, or a fully formalized K3 proof.
