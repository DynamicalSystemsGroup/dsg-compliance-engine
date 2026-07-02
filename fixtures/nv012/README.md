# `fixtures/nv012/` — mocked evidence exports for the NV012 run

These JSON files stand in for **real GCP / Google Workspace config exports**.
The mocked generators (`evidence/generators/*`, U6) read them and emit
`EvidenceArtifact`s; the oracles (`oracles/criteria.py`, U7) read each file's
`summary` dict and compare it to a machine criterion. Every artifact is marked
`evidentiary_status: "mock"` — it **addresses** a control but is **not** real
evidence (R12 non-evidentiary marker).

## Envelope schema (every file)

| Field                | Type        | Meaning                                                        |
| -------------------- | ----------- | -------------------------------------------------------------- |
| `source_system`      | string      | export origin, e.g. `workspace.2sv`, `gcp.kms`, `gcp.iam`      |
| `export_command`     | string      | the (illustrative) command that produced the raw export       |
| `collected_at`       | ISO-8601    | collection timestamp → `CollectionMetadata.collected_at`       |
| `collector_version`  | string      | mock collector version → `CollectionMetadata.collector_version`|
| `controls`           | string[]    | CMMC control id(s) this export **addresses** (`ce:addresses`)  |
| `evidentiary_status` | string      | always `"mock"` for fixtures                                   |
| `raw`                | object      | realistic GCP/Workspace-shaped payload (hashed as raw bytes)   |
| `summary`            | object      | **machine-readable** metrics the oracle reads (schema below)   |

The `source_system`, `export_command`, `collected_at`, and `collector_version`
fields map onto U6's `CollectionMetadata {source_system, export_command,
collected_at, collector_version}`.

## `summary` schema (keys = oracle `metric_key`s in `oracles/criteria.py`)

| `summary` key              | type    | criterion (control)          | passes when   |
| -------------------------- | ------- | ---------------------------- | ------------- |
| `mfa_enforced_privileged`  | bool    | `IA.L2-3.5.3` (`eq true`)    | `true`        |
| `fips_module_present`      | bool    | `SC.L2-3.13.11` (`eq true`)  | `true`        |
| `cui_encrypted_at_rest`    | bool    | `SC.L2-3.13.16` (`eq true`)  | `true`        |
| `unauthorized_principals`  | int     | `AC.L2-3.1.1` (`eq 0`)       | `0`           |
| `data_region`              | string  | `ITAR-120.54` (`eq "US"`)    | `"US"`        |

Each fixture file carries exactly one criterion's metric in its `summary`; the
generator run unions them into the per-control evidence summary.

## The three labelled sets

| Set              | Files                                                                 | Purpose (U13)                                                                                           |
| ---------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `all-covered/`   | all 5 exports, **every criterion passes**                            | happy path — Gate 1 passes, Factory completes, **SPRS 110/Final** (mock-marked).                        |
| `gap/`           | 4 exports — **omits `gcp_kms_cmvp.json`** (the FIPS evidence)        | at the **Factory/oracle** layer: with no FIPS export the `fips_module_present` metric is absent → the `SC.L2-3.13.11` oracle returns `cantTell`/absent (missing-evidence gap). NB: `SC.L2-3.13.11` still has a claiming tier1 module (`CMEK_KeyRing`), so this set does **not** by itself trip **Gate 1** — Gate 1 is a *planning* check on module coverage, not evidence. See the U13 note below. |
| `contradiction/` | all 5 exports, but `mfa_enforced_privileged: false`                  | oracle for `IA.L2-3.5.3` **fails**; when the Affirming Official attests MET the audit's contradiction dimension fires (**MET-over-failed-oracle**, R13). |

### Set file inventory

- **`all-covered/`**: `workspace_2sv.json`, `gcp_kms_cmvp.json`,
  `gcp_cmek_at_rest.json`, `gcp_iam_bindings.json`, `gcp_org_policy_region.json`
- **`gap/`**: same **minus** `gcp_kms_cmvp.json` (FIPS evidence for
  `SC.L2-3.13.11` absent → the metric `fips_module_present` never appears).
- **`contradiction/`**: same five as `all-covered/`, with the MFA export patched
  so `mfa_enforced_privileged: false` (oracle `failed`).

## End-to-end (U13) — expected end-states (`tests/test_nv012_e2e.py`)

The acceptance test drives the whole chain (compile → Gate 1 → Factory →
attest → audit → SPRS → BOM → SSP) programmatically and asserts:

| Scenario | Driver | Asserted end-state |
| -------- | ------ | ------------------ |
| **all-covered** | `evidence_set="all-covered"`; all 22 required controls attested MET | Gate 1 passes → Factory completes → **SPRS 110 / Final / `valid_submission`**; BOM + run carry `ce:evidentiaryStatus "mock"`; the SSP shows the **NON-EVIDENTIARY** banner (R12); every required control is MET and the machine-checkable subset is cited to a 64-hex evidence hash; the SSP VCRM status column equals the attestation outcomes in the graph (no drift); the registry resolves `NV012 → latest BOM → artifact hashes`. |
| **gap** | an **uncovered 5-point required control** (`AC.L2-3.1.12`, no claiming tier1 module) added at the *obligation* layer | `compile_order` raises **`Gate1Failed`**; the gap report names `AC.L2-3.1.12`; **no Order is emitted and the Factory never runs**. (This is the *planning*-gate refusal. The `gap/` evidence set above is the complementary *Factory-layer* missing-evidence gap.) |
| **contradiction** | `evidence_set="contradiction"` (oracle `IA.L2-3.5.3` = `failed`); official attests MET **without** `cmmc:overrideJustification` | the audit's **R13 contradiction dimension** flags the MET-over-failed-oracle; the report reads "0 MET-by-machine / 1 MET-by-human-only"; the SSP colophon surfaces `contradictions: 1.`; SPRS reflects the human MET call. Adding an override justification **clears** the contradiction (`contradictions: 0.`). |

Note on Gate 1 vs. evidence gaps: **Gate 1** (Order Compiler) checks that every
required control has a claiming module — a *planning*-time property, independent
of any evidence set. A missing/failed *oracle* (the `gap/` and `contradiction/`
sets) is a *Factory/Gate 2* concern surfaced later by the oracles + audit, not a
Gate-1 refusal.
