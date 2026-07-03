# The compliance engine — end-to-end walkthrough

A [marimo](https://marimo.io) notebook that runs the **real** engine and follows one
artifact all the way down the assembly line. A signed defense contract enters, and
you watch it change shape at each station — obligations, required controls, a signed
Order, the Runtime, human attestation — until it comes out the far end as the audit,
SPRS score, BOM, and SSP an assessor reads.

It is one continuous scroll, not a set of tabs. Each station shows what goes **in**
and what comes **out**, in plain English on top and with the real engine payload
underneath. A sidebar rail tracks where the artifact currently is.

Pick a scenario in the sidebar and the whole chain re-executes on the real code:

- **all-covered** — the full chain completes: SPRS 110 / Final, plus a mock BOM and SSP.
- **gap** — Gate 1 refuses and names the uncovered control; nothing is built.
- **contradiction** — a human signs MET over a *failed* machine check; the audit flags it.

Everything runs on fixture evidence with mock providers — no cloud, no credentials —
so every artifact is stamped **NON-EVIDENTIARY**.

## Run it

All commands are run from the **repo root** so the notebook can import the engine.

```bash
# one-time: install marimo (the only notebook dependency)
uv sync --group notebook
```

### Explore (interactive, editable)

```bash
uv run --group notebook marimo edit notebooks/compliance_walkthrough.py
```

Opens the notebook in marimo's editor with code cells visible. Change the **Scenario**
dropdown in the sidebar and every cell downstream re-runs.

### Present (read-only app, no code)

```bash
uv run --group notebook marimo run notebooks/compliance_walkthrough.py
```

Opens the notebook as a read-only app at `http://localhost:2718`. No code cells — just
the sidebar and the single scroll. This is the mode for demos and sharing.

### Export to a static site

```bash
uv run --group notebook marimo export html-wasm notebooks/compliance_walkthrough.py -o walkthrough/
python -m http.server --directory walkthrough/
```

Produces a self-contained static site. The WASM export runs marimo's Python runtime in
the browser via Pyodide; the engine is deterministic, so it reproduces the same numbers,
but cold-start is slower than the server-backed `marimo run`.

## What you will see

### Sidebar (always visible)

- **Scenario selector** — switch between all-covered, gap, and contradiction.
- **Where the artifact is** — a "you are here" rail over the ten stations, marking how
  far this run travelled (and where Gate 1 stopped it, in the gap scenario).
- **Live indicators** — controls required, modules claimed, Gate 1 status, SPRS score,
  the machine-vs-human split, and the contradiction count.
- **NON-EVIDENTIARY notice.**

### The scroll (twelve stations)

1. **The contract** — the NV012 contract enters; its obligations are extracted.
2. **Obligations become controls** — the rule library expands them into the required set.
3. **The Compliance Officer signs the COP** — the first human judgment (real COP fields).
4. **Gate 1 — planning coverage** — forward, backward, and no-untestable-claim; pass or
   a refusal that names the gap.
5. **The signed Order** — the one hash-referenced artifact that passes across the seam.
6. **The Runtime** — the seven-stage assembly line (load, fetch-by-hash, terraform plan
   with mock providers, policy check with the residency hard gate, mock apply, evidence,
   oracles), with the real modules, evidence, and oracle outcomes.
7. **The attested-reference model** — the centerpiece: the one uniform check (registered,
   resolves, fresh, signed-by-role) shown across a machine control and a human control on
   equal footing, with the real authoritative sources and reference records behind the 43
   Track B controls.
8. **Gate 2 — the human attests MET** — the Affirming Official's sign-off, the
   contradiction rule, and the real per-control BOM mapping.
9. **The proof outputs** — the audit, the SPRS score and its bands, the content-addressed
   BOM, and the deterministic SSP with its structural NON-EVIDENTIARY banner.
10. **Proof by reproduction** — how a C3PAO re-derives the record with `ce verify`, and how
    a one-byte change is caught by the hash.
11. **The substrate** — the eight named graphs of one RDF dataset, with live triple counts,
    and the five roles on the line.
12. **Full coverage — all 110 controls** — a filterable view of how every control is
    verified: **65** machine-verified, **43** attested-reference, **2** CSP-inherited. The
    demonstration Order runs a slice; the structural model claims the whole catalog.

## The engine adapter

[`_engine.py`](_engine.py) calls the same code paths the operator CLI (`ce`) uses — it
never reimplements engine logic. The notebook is a viewport onto the running engine. The
one clearly-fenced *illustration* panel (the override-justification flow) is labelled as
such; every other number and payload is real engine output. Coverage and the
attested-reference records are read live from the graph
(`data/structural/tier1.ttl` + `data/structural/references.ttl`), never hardcoded. Run
artifacts go to a throwaway temp directory, never the repo.

## Tests

```bash
uv run --group notebook pytest tests/test_notebook_smoke.py -v
```

Covers all three scenarios, determinism, invalid input, named-graph population, and that
the notebook file is a valid marimo app. The notebook itself is validated headlessly by
exporting each scenario and confirming every cell executes without error.
