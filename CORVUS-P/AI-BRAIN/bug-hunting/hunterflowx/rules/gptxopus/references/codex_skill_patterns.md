# Codex Skill Pattern Adaptation

This kit adapts public Codex skill design patterns locally. It does not install, vendor, or depend on third-party skills.

## OpenAI Skill Patterns Adapted

| Source pattern | Local adaptation |
|---|---|
| `security-best-practices` | Keep security guidance scoped, language/domain aware, and evidence-oriented |
| `security-threat-model` | Model assets, trust boundaries, attacker capabilities, abuse paths, and mitigations before test-cards |
| `cli-creator` | Prefer composable, deterministic inputs/outputs for repeated workflow operations |
| `playwright` | Treat browser-visible evidence as a first-class validation loop when browser testing is authorized |

## Community Security Skill Patterns Adapted

| Source pattern | Local adaptation |
|---|---|
| Threat modeling | Explicit actor, object, tenant, state, and trust-boundary mapping |
| Config hardening | Misconfiguration checks must tie exposed config to intended audience and business impact |
| Dependency risk audit | Supply-chain checks must separate metadata risk, reachability, provenance, and safe proof |
| Security quick scan | Fast passes are triage only; they cannot produce verdicts without manual evidence |

## Local Rule

The adapted patterns are procedural hints only. They cannot override program scope, source grounding, manual evidence gates, or the creative lane.
