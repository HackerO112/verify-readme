"""VeriCode - automated freshness checking for code examples in documentation.

Single-file Streamlit app:
  streamlit run app.py

Give it a URL. VeriCode scrapes the page for Python code snippets, figures out which
third-party packages each snippet needs, installs the latest versions of those packages
in a throwaway virtualenv, runs the snippet there, and reports what still works.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import venv
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

import requests
import streamlit as st
from bs4 import BeautifulSoup

APP_TITLE = "VeriCode"
USER_AGENT = "VeriCode/1.0 (documentation freshness checker)"
PYPI_JSON = "https://pypi.org/pypi/{name}/json"

# Import name -> PyPI distribution name, for the cases where they differ.
IMPORT_TO_PYPI: dict[str, str] = {
    "attr": "attrs",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dateutil": "python-dateutil",
    "django": "Django",
    "dotenv": "python-dotenv",
    "fitz": "PyMuPDF",
    "flask": "Flask",
    "google": "google-api-python-client",
    "grpc": "grpcio",
    "jinja2": "Jinja2",
    "jwt": "PyJWT",
    "MySQLdb": "mysqlclient",
    "OpenSSL": "pyOpenSSL",
    "PIL": "Pillow",
    "psycopg2": "psycopg2-binary",
    "pkg_resources": "setuptools",
    "serial": "pyserial",
    "skimage": "scikit-image",
    "sklearn": "scikit-learn",
    "slugify": "python-slugify",
    "sqlalchemy": "SQLAlchemy",
    "usb": "pyusb",
    "win32com": "pywin32",
    "yaml": "PyYAML",
    "zmq": "pyzmq",
}

# Packages we never try to install/run (huge, interactive, or dangerous in a sandbox).
BLOCKED_PACKAGES = {"tensorflow", "torch", "torchvision", "jax", "jaxlib"}

STDLIB = set(getattr(sys, "stdlib_module_names", set())) | {
    "typing_extensions",
    "__future__",
}

PROMPT_RE = re.compile(r"^\s*(>>>|\.\.\.|\$|#\s*\$)\s?")
PIP_INSTALL_RE = re.compile(
    r"(?:pip3?|python3?\s+-m\s+pip|uv\s+pip)\s+install\s+([^\n&|;]+)", re.I
)
REQ_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")

CACHE_ROOT = os.path.join(tempfile.gettempdir(), "vericode-venvs")


# --------------------------------------------------------------------------------------
# data model
# --------------------------------------------------------------------------------------
@dataclass
class Snippet:
    index: int
    code: str
    source: str = "code block"
    imports: list[str] = field(default_factory=list)
    implied_imports: list[str] = field(default_factory=list)
    declared_requirements: list[str] = field(default_factory=list)
    parse_error: str | None = None

    @property
    def preview(self) -> str:
        first = next((ln for ln in self.code.splitlines() if ln.strip()), "")
        return textwrap.shorten(first, width=70, placeholder=" ...")


@dataclass
class Result:
    index: int
    status: str  # passed | failed | skipped | install-failed
    packages: dict[str, str] = field(default_factory=dict)  # name -> version installed
    stdout: str = ""
    stderr: str = ""
    detail: str = ""
    duration: float = 0.0
    diagnosis: str = ""


# --------------------------------------------------------------------------------------
# scraping
# --------------------------------------------------------------------------------------
def fetch_html(url: str, timeout: int = 30) -> str:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.text


def _clean_snippet(raw: str) -> str:
    lines = raw.replace("\r\n", "\n").split("\n")
    if any(ln.lstrip().startswith(">>>") for ln in lines):
        # A doctest/REPL transcript: keep the input lines, drop expected output.
        kept = [
            PROMPT_RE.sub("", ln)
            for ln in lines
            if ln.lstrip().startswith((">>>", "..."))
        ]
        lines = kept
    return textwrap.dedent("\n".join(lines)).strip("\n")


def _looks_like_python(code: str) -> bool:
    if not code.strip():
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    # `hello world` parses as Python but is not a useful example.
    return bool(re.search(r"\b(import|def|class|print|for|with|=|await)\b", code))


def extract_snippets(html: str) -> list[Snippet]:
    soup = BeautifulSoup(html, "html.parser")
    blocks: list[tuple[str, str]] = []  # (code, source label)

    # Only block-level <pre> elements: inline <code> spans are almost always partial
    # expressions rather than runnable examples.
    for pre in soup.find_all("pre"):
        text = pre.get_text()
        if not text.strip():
            continue
        classes = " ".join(pre.get("class") or [])
        parent_classes = " ".join(pre.parent.get("class") or []) if pre.parent else ""
        label = f"<{pre.name}> {classes or parent_classes}".strip()
        blocks.append((text, label))

    snippets: list[Snippet] = []
    shell_requirements: list[str] = []
    seen: set[str] = set()

    for text, label in blocks:
        cleaned = _clean_snippet(text)
        if not cleaned:
            continue
        shell_requirements.extend(parse_pip_installs(cleaned))
        if len(cleaned) < 15:
            continue
        if "\n" not in cleaned and not re.match(r"\s*(import|from)\s", cleaned):
            continue
        digest = hashlib.sha1(cleaned.encode()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        if not _looks_like_python(cleaned):
            continue
        snippets.append(
            Snippet(index=len(snippets) + 1, code=cleaned, source=label)
        )

    for i, snip in enumerate(snippets):
        snip.imports = top_level_imports(snip.code)
        snip.declared_requirements = sorted(set(shell_requirements))
        snip.implied_imports = implicit_imports(snip, snippets[:i])
    return snippets


def parse_pip_installs(text: str) -> list[str]:
    """Pull package names out of `pip install ...` lines shown on the page."""
    found: list[str] = []
    for match in PIP_INSTALL_RE.finditer(text):
        for token in match.group(1).split():
            if token.startswith("-"):
                continue
            name = REQ_TOKEN_RE.match(token.strip("'\"`"))
            if name:
                found.append(name.group(0))
    return found


def top_level_imports(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return sorted(n for n in names if n and not n.startswith("_"))


def import_statements(code: str) -> dict[str, str]:
    """Map each name bound by an import to the import statement that binds it."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    bound: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            stmt = ast.unparse(node)
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound[alias.asname or alias.name.split(".")[0]] = stmt
    return bound


def referenced_names(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def implicit_imports(snippet: Snippet, earlier: list[Snippet]) -> list[str]:
    """Imports a snippet uses but doesn't repeat, recovered from earlier snippets.

    Docs routinely show `import requests` once and omit it from every later example;
    without this those examples fail with a NameError that has nothing to do with rot.
    """
    own = import_statements(snippet.code)
    used = referenced_names(snippet.code) - set(own)
    available: dict[str, str] = {}
    for prev in earlier:
        available.update(import_statements(prev.code))
    return sorted({available[name] for name in used if name in available})


def requirements_for(snippet: Snippet, use_declared: bool = True) -> list[str]:
    names = set(snippet.imports)
    for stmt in snippet.implied_imports:
        names.update(top_level_imports(stmt))
    pkgs = {IMPORT_TO_PYPI.get(name, name) for name in names if name not in STDLIB}
    if use_declared:
        declared_imports = {name.lower() for name in snippet.imports}
        for req in snippet.declared_requirements:
            # Only add a declared requirement if the snippet actually references it,
            # so one page-wide `pip install` line doesn't bloat every venv.
            if req.lower().replace("-", "_") in declared_imports:
                pkgs.add(req)
    return sorted(pkgs)


# --------------------------------------------------------------------------------------
# PyPI metadata
# --------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def latest_version(package: str) -> str | None:
    try:
        resp = requests.get(
            PYPI_JSON.format(name=package),
            timeout=15,
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        return resp.json()["info"]["version"]
    except Exception:
        return None


# --------------------------------------------------------------------------------------
# sandboxed execution
# --------------------------------------------------------------------------------------
def _venv_python(env_dir: str) -> str:
    candidate = os.path.join(env_dir, "bin", "python")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(env_dir, "Scripts", "python.exe")


def ensure_env(packages: list[str], install_timeout: int) -> tuple[str, str]:
    """Create (or reuse) a virtualenv with the latest versions of `packages`.

    Returns (path_to_python, error_message). error_message is "" on success.
    """
    key = hashlib.sha1(("|".join(sorted(packages)) + sys.version).encode()).hexdigest()[:16]
    env_dir = os.path.join(CACHE_ROOT, key)
    python = _venv_python(env_dir)
    marker = os.path.join(env_dir, ".vericode-ready")

    if os.path.exists(marker) and os.path.exists(python):
        return python, ""

    shutil.rmtree(env_dir, ignore_errors=True)
    os.makedirs(CACHE_ROOT, exist_ok=True)
    try:
        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
    except Exception as exc:  # pragma: no cover - environment dependent
        return "", f"could not create virtualenv: {exc}"

    python = _venv_python(env_dir)
    if packages:
        cmd = [python, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", *packages]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=install_timeout
            )
        except subprocess.TimeoutExpired:
            return "", f"pip install timed out after {install_timeout}s"
        if proc.returncode != 0:
            return "", (proc.stderr or proc.stdout)[-4000:]

    open(marker, "w").close()
    return python, ""


def installed_versions(python: str, packages: list[str]) -> dict[str, str]:
    if not packages:
        return {}
    code = (
        "import json\n"
        "from importlib.metadata import version, PackageNotFoundError\n"
        f"names = {packages!r}\n"
        "out = {}\n"
        "for n in names:\n"
        "    try:\n"
        "        out[n] = version(n)\n"
        "    except PackageNotFoundError:\n"
        "        out[n] = 'not installed'\n"
        "print(json.dumps(out))\n"
    )
    try:
        proc = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=60)
        return json.loads(proc.stdout.strip() or "{}")
    except Exception:
        return {n: "unknown" for n in packages}


def diagnose(stderr: str) -> str:
    if not stderr:
        return ""
    tail = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    checks = [
        (r"ImportError: cannot import name '([^']+)' from '([^']+)'",
         lambda m: f"`{m.group(1)}` no longer exists in `{m.group(2)}` — likely moved or renamed in a newer release."),
        (r"ModuleNotFoundError: No module named '([^']+)'",
         lambda m: f"Module `{m.group(1)}` is missing — the package may have been renamed, split, or dropped."),
        (r"AttributeError: module '([^']+)' has no attribute '([^']+)'",
         lambda m: f"`{m.group(1)}.{m.group(2)}` was removed or renamed in the current version."),
        (r"AttributeError: '([^']+)' object has no attribute '([^']+)'",
         lambda m: f"`{m.group(2)}` is gone from `{m.group(1)}` — API changed since the docs were written."),
        (r"TypeError: .*unexpected keyword argument '([^']+)'",
         lambda m: f"Keyword argument `{m.group(1)}` was removed or renamed in the current version."),
        (r"DeprecationWarning|DeprecatedWarning",
         lambda m: "Deprecation warning raised — the example still runs but uses a deprecated API."),
        (r"(ConnectionError|MaxRetryError|NameResolutionError|SSLError|socket\.gaierror|urlopen error)",
         lambda m: "Network access failed — this example likely needs internet or a live service, not a broken API."),
        (r"(KeyError: '?[A-Z_]{3,}'?|EnvironmentError|MissingCredentials|Unauthorized|401|403)",
         lambda m: "Looks like missing credentials/config rather than an outdated API."),
        (r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'",
         lambda m: f"Example expects a local file `{m.group(1)}` that does not exist here."),
        (r"SyntaxError",
         lambda m: "The snippet is not valid Python for this interpreter — possibly truncated in the docs."),
        (r"NameError: name '([^']+)' is not defined",
         lambda m: f"`{m.group(1)}` is undefined — the snippet is probably a fragment that relies on "
                   "earlier code on the page (try enabling snippet chaining)."),
    ]
    for pattern, fmt in checks:
        m = re.search(pattern, stderr)
        if m:
            return fmt(m)
    return f"Unclassified failure: {tail}" if tail else ""


def build_preamble(snippet: Snippet, chained: list[str], auto_imports: bool) -> str:
    parts: list[str] = []
    if auto_imports:
        parts.extend(snippet.implied_imports)
    parts.extend(chained)
    return "\n".join(parts)


def run_snippet(
    snippet: Snippet,
    install_timeout: int,
    run_timeout: int,
    allow_network: bool,
    use_declared: bool,
    preamble: str = "",
) -> Result:
    started = time.time()
    packages = requirements_for(snippet, use_declared=use_declared)
    blocked = [p for p in packages if p.lower() in BLOCKED_PACKAGES]
    if blocked:
        return Result(
            index=snippet.index,
            status="skipped",
            detail=f"Skipped: heavyweight dependency not installed in sandbox ({', '.join(blocked)}).",
            duration=time.time() - started,
        )

    python, err = ensure_env(packages, install_timeout)
    if err:
        return Result(
            index=snippet.index,
            status="install-failed",
            stderr=err,
            detail="Dependencies could not be installed at their latest versions.",
            diagnosis=diagnose(err),
            duration=time.time() - started,
        )

    versions = installed_versions(python, packages)

    workdir = tempfile.mkdtemp(prefix="vericode-run-")
    script = os.path.join(workdir, "snippet.py")
    with open(script, "w") as fh:
        if preamble:
            fh.write(preamble.rstrip() + "\n")
        fh.write(snippet.code + "\n")

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": workdir,
        "TMPDIR": workdir,
        "LANG": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONWARNINGS": "default",
    }
    if not allow_network:
        # No real sandbox: point network traffic at a dead proxy so snippets fail fast
        # instead of hanging or hitting third-party services.
        env["http_proxy"] = env["https_proxy"] = "http://127.0.0.1:9"
        env["no_proxy"] = ""

    try:
        proc = subprocess.run(
            [python, script],
            capture_output=True,
            text=True,
            timeout=run_timeout,
            cwd=workdir,
            env=env,
        )
        status = "passed" if proc.returncode == 0 else "failed"
        result = Result(
            index=snippet.index,
            status=status,
            packages=versions,
            stdout=proc.stdout[-6000:],
            stderr=proc.stderr[-6000:],
            duration=time.time() - started,
        )
        if status == "failed":
            result.detail = f"Exited with code {proc.returncode}."
            result.diagnosis = diagnose(proc.stderr)
        elif "Warning" in proc.stderr:
            result.diagnosis = diagnose(proc.stderr)
    except subprocess.TimeoutExpired:
        result = Result(
            index=snippet.index,
            status="failed",
            packages=versions,
            detail=f"Timed out after {run_timeout}s.",
            diagnosis="Snippet did not terminate — it may start a server or wait for input.",
            duration=time.time() - started,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return result


# --------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------
STATUS_ICON = {
    "passed": "PASS",
    "failed": "FAIL",
    "skipped": "SKIP",
    "install-failed": "DEPS",
}


def build_report(url: str, snippets: list[Snippet], results: list[Result]) -> dict[str, Any]:
    by_index = {s.index: s for s in snippets}
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    checked = counts.get("passed", 0) + counts.get("failed", 0)
    score = round(100 * counts.get("passed", 0) / checked) if checked else None
    return {
        "url": url,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "freshness_score": score,
        "counts": counts,
        "snippets": [
            {
                **asdict(by_index[r.index]),
                "result": asdict(r),
            }
            for r in results
        ],
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# VeriCode Freshness Report",
        "",
        f"- **Source:** {report['url']}",
        f"- **Generated:** {report['generated_at']}",
        f"- **Python:** {report['python']}",
        f"- **Freshness score:** {report['freshness_score'] if report['freshness_score'] is not None else 'n/a'}%",
        "- **Totals:** " + ", ".join(f"{k}: {v}" for k, v in sorted(report["counts"].items())),
        "",
        "| # | Status | Packages (latest) | Diagnosis |",
        "| - | ------ | ----------------- | --------- |",
    ]
    for item in report["snippets"]:
        res = item["result"]
        pkgs = ", ".join(f"{k}=={v}" for k, v in res["packages"].items()) or "stdlib only"
        note = (res["diagnosis"] or res["detail"] or "").replace("|", "\\|")
        lines.append(f"| {item['index']} | {res['status']} | {pkgs} | {note} |")
    lines.append("")
    for item in report["snippets"]:
        res = item["result"]
        if res["status"] == "passed":
            continue
        lines += [
            f"## Snippet {item['index']} — {res['status']}",
            "",
            "```python",
            item["code"],
            "```",
            "",
        ]
        if res["stderr"]:
            lines += ["```text", res["stderr"].strip(), "```", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧪", layout="wide")
    st.title("🧪 VeriCode")
    st.caption(
        "Paste a tutorial, blog post, or docs URL. VeriCode extracts the Python examples, "
        "installs the latest versions of what they import, runs them in throwaway virtualenvs, "
        "and reports what still works."
    )

    with st.sidebar:
        st.header("Settings")
        run_timeout = st.slider("Run timeout per snippet (s)", 5, 120, 30, 5)
        install_timeout = st.slider("Install timeout per snippet (s)", 30, 900, 300, 30)
        max_snippets = st.number_input("Max snippets to run", 1, 50, 10)
        allow_network = st.checkbox("Allow network access in snippets", value=False)
        use_declared = st.checkbox("Use `pip install` lines found on the page", value=True)
        auto_imports = st.checkbox(
            "Re-add imports declared earlier on the page",
            value=True,
            help="Docs usually show `import x` once; later examples assume it. Without this "
                 "they fail with NameError for reasons unrelated to documentation rot.",
        )
        chain = st.checkbox(
            "Chain snippets (run earlier snippets as setup context)",
            value=False,
            help="Docs often split one example across several blocks; chaining prepends the "
                 "earlier selected snippets before running each one.",
        )
        st.divider()
        if st.button("Clear virtualenv cache"):
            shutil.rmtree(CACHE_ROOT, ignore_errors=True)
            st.success("Cache cleared.")
        st.caption(
            "Snippets run as your local user in a temp dir — only check sources you trust."
        )

    url = st.text_input(
        "Documentation URL",
        placeholder="https://example.com/some-python-tutorial",
    )
    col_a, col_b = st.columns([1, 5])
    scan = col_a.button("Scan page", type="primary", use_container_width=True)

    if scan:
        if not url.strip().startswith(("http://", "https://")):
            st.error("Enter a full URL starting with http:// or https://")
            return
        with st.spinner("Fetching and parsing page..."):
            try:
                html = fetch_html(url.strip())
            except Exception as exc:
                st.error(f"Could not fetch the page: {exc}")
                return
            snippets = extract_snippets(html)
        st.session_state["url"] = url.strip()
        st.session_state["snippets"] = snippets
        st.session_state.pop("report", None)

    snippets: list[Snippet] = st.session_state.get("snippets", [])
    if not snippets:
        if st.session_state.get("url"):
            st.warning("No runnable Python snippets found on that page.")
        return

    st.subheader(f"Found {len(snippets)} Python snippet(s)")
    selected: list[int] = []
    for snip in snippets:
        reqs = requirements_for(snip, use_declared=use_declared)
        label = f"#{snip.index} · {snip.preview}"
        with st.expander(label, expanded=False):
            st.code(snip.code, language="python")
            st.write(
                "**Third-party requirements:** "
                + (", ".join(f"`{r}`" for r in reqs) if reqs else "_stdlib only_")
            )
            if snip.implied_imports and auto_imports:
                st.caption(
                    "Implied from earlier snippets: "
                    + ", ".join(f"`{s}`" for s in snip.implied_imports)
                )
            if reqs:
                cols = st.columns(min(len(reqs), 4))
                for i, pkg in enumerate(reqs):
                    ver = latest_version(pkg)
                    cols[i % len(cols)].metric(pkg, ver or "not on PyPI")
            if st.checkbox("Verify this snippet", value=snip.index <= max_snippets, key=f"sel-{snip.index}"):
                selected.append(snip.index)

    st.divider()
    if st.button(f"Verify {len(selected)} snippet(s)", type="primary", disabled=not selected):
        chosen = [s for s in snippets if s.index in selected]
        results: list[Result] = []
        preamble_parts: list[str] = []
        progress = st.progress(0.0, text="Starting...")
        live = st.container()
        for i, snip in enumerate(chosen, start=1):
            progress.progress(
                (i - 1) / len(chosen), text=f"Snippet #{snip.index}: installing & running..."
            )
            res = run_snippet(
                snip,
                install_timeout=install_timeout,
                run_timeout=run_timeout,
                allow_network=allow_network,
                use_declared=use_declared,
                preamble=build_preamble(snip, preamble_parts if chain else [], auto_imports),
            )
            if chain:
                preamble_parts.append(snip.code)
            results.append(res)
            live.write(
                f"**#{snip.index}** {STATUS_ICON.get(res.status, res.status)} "
                f"({res.duration:.1f}s) {res.diagnosis or res.detail}"
            )
        progress.progress(1.0, text="Done.")
        st.session_state["report"] = build_report(st.session_state["url"], snippets, results)

    report = st.session_state.get("report")
    if not report:
        return

    st.header("Freshness report")
    counts = report["counts"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Freshness score", f"{report['freshness_score']}%" if report["freshness_score"] is not None else "n/a")
    c2.metric("Passed", counts.get("passed", 0))
    c3.metric("Failed", counts.get("failed", 0) + counts.get("install-failed", 0))
    c4.metric("Skipped", counts.get("skipped", 0))

    st.dataframe(
        [
            {
                "#": item["index"],
                "status": item["result"]["status"],
                "seconds": round(item["result"]["duration"], 1),
                "packages": ", ".join(
                    f"{k}=={v}" for k, v in item["result"]["packages"].items()
                )
                or "stdlib only",
                "diagnosis": item["result"]["diagnosis"] or item["result"]["detail"],
            }
            for item in report["snippets"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    for item in report["snippets"]:
        res = item["result"]
        with st.expander(f"#{item['index']} — {res['status']}", expanded=res["status"] != "passed"):
            st.code(item["code"], language="python")
            if res["diagnosis"]:
                (st.success if res["status"] == "passed" else st.error)(res["diagnosis"])
            elif res["detail"]:
                st.info(res["detail"])
            if res["stdout"]:
                st.text_area("stdout", res["stdout"], height=120, key=f"out-{item['index']}")
            if res["stderr"]:
                st.text_area("stderr", res["stderr"], height=180, key=f"err-{item['index']}")

    md = report_markdown(report)
    d1, d2 = st.columns(2)
    d1.download_button("Download Markdown report", md, file_name="vericode-report.md", mime="text/markdown")
    d2.download_button(
        "Download JSON report",
        json.dumps(report, indent=2),
        file_name="vericode-report.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()
