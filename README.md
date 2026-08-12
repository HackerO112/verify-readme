<div align="center">

# 🔍 VeriCode

### *Automated freshness checking for Python code examples in documentation.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Paste a URL. Get a freshness report. Sleep well.**

VeriCode scrapes docs for Python snippets, spins up a throwaway virtualenv with the
**latest** versions of every third-party package, runs each snippet, and tells you
exactly what broke — and why.

[Getting Started](#-getting-started) · [How It Works](#-how-it-works) · [Caveats](#-caveats)

</div>

---

## 🚀 Getting Started

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it. A browser tab opens. Drop in a URL. Watch the magic.

---

## ⚙️ How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   URL Input  │────▶│  Scrape & Parse  │────▶│  Resolve Deps   │────▶│  Execute in  │
│             │     │  <pre> blocks    │     │  AST → PyPI     │     │  throwaway   │
└─────────────┘     │  >>> → script    │     │  latest versions│     │  virtualenv  │
                    └──────────────────┘     └─────────────────┘     └──────┬───────┘
                                                                            │
                    ┌──────────────────┐     ┌─────────────────┐           │
                    │  Freshness       │◀────│  Diagnose       │◀──────────┘
                    │  Report          │     │  Classify       │
                    │  · Score         │     │  tracebacks     │
                    │  · Per-snippet   │     │  plain English  │
                    │  · MD / JSON dl  │     │  explanations   │
                    └──────────────────┘     └─────────────────┘
```

### 1. Scrape — *only what matters*
- Targets `<pre>` blocks exclusively — no navigation soup, no inline code noise.
- Doctest/REPL transcripts (`>>> `) are automatically converted to plain scripts; expected output is dropped.
- Non-Python blocks are filtered out via `ast.parse` — if it doesn't parse, it doesn't run.

### 2. Resolve Dependencies — *AST → PyPI, no guessing*
- Top-level imports extracted via AST, mapped to real PyPI distribution names:

| Import | Resolves To |
|--------|-------------|
| `bs4` | `beautifulsoup4` |
| `PIL` | `Pillow` |
| `cv2` | `opencv-python` |
| `sklearn` | `scikit-learn` |
| `yaml` | `PyYAML` |
| … | [full map](#) |

- Stdlib imports are ignored entirely.
- `pip install` lines found on the page are used as a secondary signal.
- Latest version numbers are pulled live from the **PyPI JSON API**.

### 3. Execute — *clean room, every time*
- One cached virtualenv **per unique dependency set**.
- `pip install --upgrade` to guarantee *latest* packages.
- Snippet runs as a subprocess in a temp `cwd` with its own timeout.
- 🌐 **Network blocked by default** — toggle in the sidebar if needed.

### 4. Diagnose — *not just "it failed"*

Every traceback is classified into a human-readable category:

| Diagnosis | Meaning |
|-----------|---------|
| 🔴 Removed / Renamed API | The function or class no longer exists in the latest version |
| 🔴 Dropped Keyword Argument | An argument was removed or renamed |
| 🟡 Missing Module | A sub-module was reorganized or removed |
| 🟡 Network / Credential Required | Snippet needs API keys or internet access |
| 🟠 Non-Terminating | Example runs past the timeout |
| 🔵 Fragment Dependency | Snippet relies on variables defined in earlier code on the page |

---

## 🧩 Handling the Hardest False Failure

Docs often show `import x` once, then omit it in later snippets. Two modes fix this:

| Mode | Behavior |
|------|----------|
| **Re-add imports** *(default on)* | Prepends only the needed `import` statements — lightweight, no side effects |
| **Chain snippets** | Runs all earlier snippets as setup before the current one — thorough but slower |

---

## ⚠️ Caveats

> **Security first.** Snippets execute as your local user in a temp directory.
> Only scan sources you trust.

- Very heavy dependencies (`torch`, `tensorflow`, `jax`, …) are **skipped** rather than installed — nobody has time for that.
- Snippets that mutate global state or depend on a specific file tree will fail even if the code is "fresh" — this is by design.
- Some docs use syntax highlighting classes instead of `<pre>` — those snippets won't be found.

---

<div align="center">
  
**built by a student who asked AI the right questions**

*Your docs are lying to your users. VeriCode catches them in the act.*

</div>
