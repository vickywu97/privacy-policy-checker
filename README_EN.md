[![CI](https://github.com/vickywu97/privacy-policy-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/vickywu97/privacy-policy-checker/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# privacy-policy-checker

**Offline privacy-policy compliance checker** — feed it a privacy policy text; it checks each clause against the PIPL (Personal Information Protection Law) and GDPR checklists item by item, and outputs a gap list + risk grading + article-level evidence.

> One-line positioning: a "privacy-policy translator" between lawyers and compliance teams. General AI fabricates statutes (proven unreliable by the author's `legal-hallucination-bench`); this tool uses only deterministic keyword matching + verbatim statute text — zero LLM dependency, offline, reproducible.

---

## Why it exists

Every app / website / SaaS must have a privacy policy, yet most have compliance gaps:

- **Incomplete notice obligations**: processor identity, purpose, retention period, and rights-exercise methods not disclosed
- **Missing separate consent**: sensitive personal info, cross-border transfer, and third-party sharing without separate consent
- **Missing user rights**: no notice of access, copy, correction, deletion, or portability rights
- **Undisclosed cross-border transfer**: overseas recipients and safeguards not disclosed

Consequences: PIPL fines up to 5% of prior-year revenue; GDPR up to 4% of global revenue or €20M, plus possible takedown / blocked financing.

---

## Install & usage

Zero third-party dependencies — Python standard library only. Requires Python 3.8+.

```
# Run directly as a module
python -m privacy_policy_checker --file path/to/privacy_policy.txt

# PIPL only
python -m privacy_policy_checker --file policy.txt --laws PIPL

# Output engineering JSON
python -m privacy_policy_checker --file policy.txt --format json -o report.json
```

Argument reference:

| Argument | Notes |
|----------|-------|
| `--file` / `-f` | Privacy policy text path (required) |
| `--laws` | Law libraries, default `PIPL GDPR`, either selectable |
| `--format` | `md` (legal Markdown, default) or `json` (engineering) |
| `--project-name` | Project name shown in the report |
| `-o` / `--output` | Output to a file, otherwise prints to stdout |

---

## Judgment model

Each checklist item returns one of four states:

- **satisfied**: clear evidence keyword found
- **partial**: only auxiliary words hit, no clear evidence
- **missing**: no evidence found
- **not_applicable**: context-conditional items (e.g. "cross-border transfer") auto-judged not-applicable when the text has no relevant context, avoiding false positives

Risk grading: an item's `risk_if_missing` is its "risk when missing"; `partial` auto-downgrades one level (high→medium); satisfied / NA are not counted as risk.

---

## Checklist library

| Law | Items | Coverage |
|-----|-------|----------|
| PIPL | 31 | Notice (Art.17), third-party sharing (23), automated decision (24), sensitive PI (29-30), minors (31), cross-border (38-39), individual rights (44-50), security measures (51), impact assessment (55), breach notice (57), periodic audit (54), legal liability (66) |
| GDPR | 42 | Principles (5), lawful basis (6-7,9), transparency (12-14), notice (13-14), data-subject rights (15-22), security (32), breach (33-34), DPIA (35), DPO (37), cross-border (44-49), complaint & fines (77,83) |

Every checklist item carries **verbatim statute text + source URL + verification date** — traceable and auditable.

---

## Legal boundary

This report is the output of an automated compliance-checking tool, for self-assessment and gap analysis, and **does not constitute legal advice**. Final compliance judgments should be made by a licensed attorney.

---

## Portfolio relationship

| Project | Compliance domain | Judgment nature |
|---------|-------------------|-----------------|
| [oss-license-checker](https://github.com/vickywu97/oss-license-checker) | IP / open-source legal | Hard rules (compatibility matrix) |
| [token-classifier](https://github.com/vickywu97/token-classifier) | Web3 / crypto legal | Soft rules (Howey four factors) |
| **privacy-policy-checker** | Data / privacy legal | Semi-hard rules (checklist) |

Together they form a complete "legal + engineering" portfolio, targeting in-house legal / data-compliance legal roles.

---

## Roadmap

- [ ] English privacy-policy dedicated checklist (synonym expansion)
- [ ] URL fetch mode (user supplies an exact URL, single GET, respects robots.txt)
- [ ] Industry templates (finance / healthcare / children's data)
- [ ] GitHub Pages online demo
- [ ] `--fail-on high` flag (CI integration)

---

## License

MIT — authored by a lawyer / tax adviser / patent attorney, open-sourced as a job-hunting portfolio.
