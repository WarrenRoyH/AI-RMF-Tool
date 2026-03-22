# AI-RMF Platform Compatibility Matrix

This document outlines the system requirements and compatibility status for AI-RMF-Tools across different operating systems.

## 1. Supported Platforms

| Platform | Tier | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Ubuntu 24.04+** | Tier 1 | ✅ Fully Supported | Primary development & testing environment. |
| **Debian 12+** | Tier 1 | ✅ Fully Supported | Compatible with Ubuntu requirements. |
| **macOS (Intel/Apple Silicon)** | Tier 1 | ✅ Fully Supported | Tested on macOS 14+ (Sonoma/Sequoia). |
| **Windows (WSL2)** | Tier 2 | ✅ Supported | Requires Ubuntu/Debian distribution in WSL2. |
| **Windows (Native)** | Tier 3 | ⚠️ Experimental | Partial functionality; `bwrap` and shell scripts unavailable. |

---

## 2. Core Dependencies

### 2.1 System Level
- **Python 3.11+**: Required for core logic and dependencies.
- **uv**: Recommended for fast, isolated dependency management.
- **Node.js / npm**: Required for `promptfoo` benchmarking.
- **cairo**: Required for PDF report generation (`xhtml2pdf`).
  - *Ubuntu/Debian*: `sudo apt install libcairo2`
  - *macOS*: `brew install cairo`

### 2.2 Sandboxing & Security
- **Bubblewrap (`bwrap`)**: Required for Linux process isolation.
  - *Ubuntu/Debian*: `sudo apt install bubblewrap`
- **sandbox-exec**: Native to macOS; used automatically when available.

---

## 3. Component Compatibility

| Component | Linux (Ubuntu/Debian) | macOS | Windows (WSL2) |
| :--- | :---: | :---: | :---: |
| **GOVERN (Librarian)** | ✅ | ✅ | ✅ |
| **MAP (Adversary)** | ✅ | ✅ | ✅ |
| **MANAGE (Sentry)** | ✅ | ✅ | ✅ |
| **MEASURE (Auditor)** | ✅ | ✅ | ✅ |
| **AUTOPILOT** | ✅ | ✅ | ✅ |
| **REMEDIATE** | ✅ | ✅ | ✅ |
| **DASHBOARD (GUI)** | ✅ | ✅ | ✅ |
| **RED TEAM (Garak)** | ✅ | ✅ | ✅ |
| **HEALTH CHECK** | ✅ | ✅ | ✅ |

---

## 4. Hardware Recommendations

- **CPU**: 4+ Cores recommended for running local LLM-Guard scanners.
- **RAM**: 8GB+ RAM (16GB+ recommended for running Garak/Promptfoo).
- **GPU**: NVIDIA GPU with 8GB+ VRAM recommended for local inference (Ollama/vLLM), but not strictly required for the toolkit itself (uses API by default).

---

## 5. Troubleshooting by Platform

### macOS
- If `xhtml2pdf` fails to install or run, ensure `cairo` is installed via Homebrew.
- Some `llm-guard` models may run slower on Intel Macs compared to Apple Silicon.

### Linux
- Ensure `bubblewrap` is installed for the `sentry` proxy to function in protected mode.

### Windows (WSL2)
- Ensure your WSL2 distribution has sufficient memory allocated (at least 8GB).
- Local networking between WSL2 and Windows might require firewall adjustments for the Dashboard.
