# Hylton Compliance Portal Architecture (Phase 20)

## 1. Overview
The **Hylton Compliance Portal** is a centralized interface for AI risk governance, separating the **Auditor** (Reasoning/Decision-making) from the **Target** (System Under Test). 

## 2. Multi-Tier Key Architecture
To ensure zero-trust, keys are categorized into two tiers:
1.  **Auditor Keys**: Long-term credentials used by the AI-RMF Auditor to communicate with its reasoning LLMs (Gemini, Claude, GPT-5).
2.  **Target Keys**: Ephemeral, project-specific keys used to access the AI application under test. These are NEVER stored in the Auditor context.

## 3. Zero-Trust Vaulting Strategy
- **Ephemeral Isolation**: Target keys are vaulted in a temporary session-scoped storage.
- **Proxy Access**: All requests from the Auditor to the Target MUST pass through the `Sentry` proxy, which injects the target keys from the vault.
- **Immutable Logic**: Security logic in `core/vault.py` handles the injection and rotation of these keys, ensuring the Auditor cannot leak them.

## 4. Proof-of-Integrity Storage
- All interactions (Auditor queries, Target responses, Sentry risk scores) are logged and checksummed.
- **Evidence Registry**: A `manifest_checksums.json` is generated for every session, registering SHA-256 hashes of all artifacts.
- **Tamper-Evident Logs**: Logs are signed to prevent post-hoc modification.

## 5. NIST Alignment
- **Govern 1.2**: Establishes organizational risk governance boundaries.
- **Map 2.2**: Maps components and their respective security tiers.
