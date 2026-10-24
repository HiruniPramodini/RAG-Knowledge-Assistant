"""Presentation layer for the Enterprise AI Knowledge Assistant (Streamlit).

Contains the design system (CSS), real document/index metadata helpers, and
reusable render functions for messages, source cards, and document rows.

Styling note: Streamlit renders every ``st.markdown`` call as its own element,
so HTML wrapper <div>s cannot enclose widgets. All widget styling here targets
either Streamlit's stable ``data-testid`` attributes or the ``st-key-<key>``
class that ``st.container(key=...)`` adds to its element.

No company facts are hardcoded in this module. Everything shown about
documents comes from files on disk or from the ChromaDB index.
"""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from src.config import BASE_DIR, RAW_DOCS_DIR

# -----------------------------------------------------------------------------
# DESIGN SYSTEM
# -----------------------------------------------------------------------------

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #6938F5;
    --accent: #7C3AED;
    --sidebar: #25145F;
    --navy: #17143A;
    --bg: #F8F7FF;
    --white: #FFFFFF;
    --lavender: #EEE8FF;
    --border: #E6E0FF;
    --muted: #716D91;
    --shadow: 0 1px 2px rgba(23, 20, 58, 0.04), 0 4px 14px rgba(105, 56, 245, 0.05);
    --shadow-hover: 0 6px 22px rgba(105, 56, 245, 0.14);
}

html, body, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stMarkdownContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Ensure Material Symbols and Icons font is protected from being overridden */
[data-testid="stIconMaterial"],
[data-testid="stIconMaterial"] *,
.material-symbols-rounded,
.material-icons {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
}

/* Styled expander with clear spacing to prevent any overlapping text */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: #FAF9FF !important;
    margin-top: 0.5rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] details summary {
    padding: 0.55rem 0.85rem !important;
    color: var(--navy) !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
[data-testid="stExpander"] details summary:hover {
    color: var(--primary) !important;
}
[data-testid="stExpander"] details summary [data-testid="stIconMaterial"] {
    color: var(--primary) !important;
    flex-shrink: 0 !important;
}

.stApp {
    background:
        radial-gradient(1200px 500px at 70% -10%, rgba(124, 58, 237, 0.08), transparent 60%),
        var(--bg);
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] {
    max-width: 1320px;
    padding-top: 2.2rem;
    padding-bottom: 7rem;
}

/* ---------------------------------------------------------------- Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2A1769 0%, #25145F 45%, #1E104F 100%);
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.5rem; }

.brand {
    display: flex; align-items: center; gap: 12px;
    padding: 0 0 1.1rem 0; margin-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand-mark {
    width: 38px; height: 38px; border-radius: 11px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #8B5CF6, #6938F5);
    color: #fff; font-size: 18px;
    box-shadow: 0 6px 16px rgba(105, 56, 245, 0.45);
}
.brand-name { color: #fff; font-weight: 700; font-size: 1rem; line-height: 1.15; }
.brand-sub { color: #B5A8EB; font-size: 0.8rem; }

/* All sidebar buttons: left-aligned nav rows */
[data-testid="stSidebar"] .stButton button {
    justify-content: flex-start;
    text-align: left;
    min-height: 2.35rem;
    padding: 0.4rem 0.8rem;
    border-radius: 9px;
    font-size: 0.9rem;
    font-weight: 500;
    width: 100%;
}
[data-testid="stSidebar"] .stButton button p {
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* Inactive nav (tertiary) */
[data-testid="stSidebar"] .stButton button[kind="tertiary"] {
    color: #CFC5FA;
    background: transparent;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stButton button[kind="tertiary"]:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.07);
}
/* Active nav (secondary) */
[data-testid="stSidebar"] .stButton button[kind="secondary"] {
    color: #FFFFFF;
    background: linear-gradient(90deg, rgba(124, 58, 237, 0.55), rgba(105, 56, 245, 0.25));
    border: 1px solid rgba(167, 139, 250, 0.35);
    font-weight: 600;
}
/* New chat action button: clean enterprise action button, not a persistent active tab */
.st-key-new_chat .stButton button {
    justify-content: center;
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    min-height: 2.45rem !important;
    border-radius: 9px !important;
    box-shadow: none !important;
    transition: all 0.18s ease-in-out !important;
}
.st-key-new_chat .stButton button:hover {
    background: linear-gradient(135deg, #7C3AED 0%, #6938F5 100%) !important;
    border-color: rgba(167, 139, 250, 0.5) !important;
    box-shadow: 0 4px 14px rgba(105, 56, 245, 0.4) !important;
    color: #FFFFFF !important;
    transform: translateY(-1px);
}

.side-label {
    color: #9D8FE0; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.07em; text-transform: uppercase;
    margin: 1.1rem 0 0.35rem 0.2rem;
}
.side-date { color: #8B7DCB; font-size: 0.72rem; font-weight: 600; margin: 0.5rem 0 0.1rem 0.2rem; }
.side-empty { color: #8B7DCB; font-size: 0.8rem; padding: 0.2rem 0.2rem; }
.side-status {
    margin-top: 1.2rem; padding: 0.7rem 0.8rem; border-radius: 10px;
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08);
    color: #CFC5FA; font-size: 0.78rem; line-height: 1.45;
}
.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.dot-ok { background: #34D399; }
.dot-bad { background: #F87171; }

/* ----------------------------------------------------------- Page header */
.page-title { font-size: 1.45rem; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.2; }
.page-sub { font-size: 0.9rem; color: var(--muted); margin-top: 0.2rem; }

/* ------------------------------------------------------------------ Hero */
.hero { text-align: center; padding: 1.6rem 0 1.4rem 0; }
.hero h1 {
    font-size: 2.15rem; font-weight: 800; color: var(--navy);
    margin: 0 0 0.5rem 0; padding: 0; letter-spacing: -0.02em;
}
.hero h1 span { color: var(--primary); }
.hero p { color: var(--muted); font-size: 1rem; margin: 0; }

/* Quick action cards */
.st-key-quick_actions .stButton button {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow);
    min-height: 118px;
    height: 100%;
    padding: 1rem 1.05rem;
    justify-content: flex-start;
    align-items: flex-start;
    text-align: left;
    color: var(--navy);
    transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
}
.st-key-quick_actions .stButton button:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
    color: var(--navy);
}
.st-key-quick_actions .stButton button [data-testid="stMarkdownContainer"] p {
    text-align: left; font-size: 0.84rem; color: var(--muted); line-height: 1.4; margin: 0;
}
.st-key-quick_actions .stButton button [data-testid="stMarkdownContainer"] p strong {
    display: block; color: var(--navy); font-size: 0.95rem; font-weight: 700; margin-bottom: 0.3rem;
}
.st-key-quick_actions .stButton button [data-testid="stIconMaterial"] {
    color: var(--primary);
    background: var(--lavender);
    border-radius: 9px;
    padding: 6px;
    font-size: 1.25rem;
}

/* Recent chats on home */
.section-label { font-size: 0.78rem; font-weight: 700; color: var(--muted);
    letter-spacing: 0.06em; text-transform: uppercase; margin: 1.6rem 0 0.5rem 0; }

/* ---------------------------------------------------------------- Chat */
[class*="st-key-msg_user_"] { align-items: flex-end; }
[class*="st-key-msg_user_"] [data-testid="stChatMessage"] {
    flex-direction: row-reverse;
    background: var(--lavender);
    border: 1px solid #DED4FD;
    border-radius: 16px 16px 4px 16px;
    max-width: min(78%, 720px);
    margin-left: auto;
    padding: 0.75rem 1rem;
}
[class*="st-key-msg_user_"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    margin-bottom: 0;
}
[class*="st-key-msg_asst_"] [data-testid="stChatMessage"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 4px 16px 16px 16px;
    box-shadow: var(--shadow);
    padding: 1rem 1.15rem;
}
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"],
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
    background: linear-gradient(135deg, #7C3AED, #6938F5);
    color: #fff;
}
.msg-time { font-size: 0.72rem; color: var(--muted); text-align: right; margin-top: -0.2rem; }

.route {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
    padding: 0.18rem 0.55rem; border-radius: 6px; margin-bottom: 0.35rem;
}
.route-rag { background: var(--lavender); color: var(--primary); }
.route-direct { background: #F1F1F8; color: #49456B; }
.route-clarify { background: #FEF3C7; color: #B45309; }
.route-tool_calculator { background: #E0F2FE; color: #0369A1; }
.route-error { background: #FEE2E2; color: #B91C1C; }

/* Inline source chips under an answer */
.src-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.4rem 0 0.2rem 0; }
.src-chip {
    display: inline-flex; align-items: center; gap: 9px;
    background: #FAF9FF; border: 1px solid var(--border); border-radius: 10px;
    padding: 0.45rem 0.7rem; max-width: 100%;
}
.src-chip .ico {
    width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
    background: var(--lavender); color: var(--primary);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.62rem; font-weight: 800;
}
.src-chip .t { font-size: 0.82rem; font-weight: 600; color: var(--navy); line-height: 1.2; }
.src-chip .c { font-size: 0.72rem; color: var(--muted); }
.src-chip .n {
    margin-left: 4px; font-size: 0.68rem; font-weight: 700; color: var(--primary);
    background: var(--lavender); border-radius: 5px; padding: 0.1rem 0.4rem;
}

/* Follow-up chips */
.st-key-followups .stButton button {
    border-radius: 999px;
    background: var(--white);
    border: 1px solid var(--border);
    color: #49456B;
    font-size: 0.82rem;
    min-height: 2.1rem;
    padding: 0.2rem 0.9rem;
}
.st-key-followups .stButton button:hover {
    border-color: var(--primary); color: var(--primary); background: #F4F0FF;
}

/* Bottom composer */
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stBottomBlockContainer"] {
    max-width: 1320px;
    background: linear-gradient(180deg, rgba(248, 247, 255, 0) 0%, var(--bg) 35%);
    padding-bottom: 1.2rem;
}
[data-testid="stChatInput"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: 0 6px 24px rgba(105, 56, 245, 0.08);
}
[data-testid="stChatInput"]:focus-within { border-color: var(--primary); }
[data-testid="stChatInputSubmitButton"] {
    background: var(--primary); color: #fff; border-radius: 10px;
}
[data-testid="stChatInputSubmitButton"]:hover { background: var(--accent); }

/* ----------------------------------------------------- Right source panel */
.st-key-source_panel {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 16px;
    box-shadow: var(--shadow);
    padding: 1.1rem 1rem;
    position: sticky;
    top: 1rem;
}
.panel-title { font-size: 1.05rem; font-weight: 700; color: var(--navy); margin: 0; }
.panel-sub { font-size: 0.8rem; color: var(--muted); margin: 0.15rem 0 0.4rem 0; }
[class*="st-key-src_card_"] {
    background: #FAF9FF;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.8rem 0.85rem 0.3rem 0.85rem;
    gap: 0.35rem;
}
[class*="st-key-src_card_"]:hover { border-color: #CDBEFD; }
.sc-head { display: flex; align-items: flex-start; gap: 10px; }
.sc-head .ico {
    width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
    background: var(--lavender); color: var(--primary);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.64rem; font-weight: 800;
}
.sc-title { font-size: 0.86rem; font-weight: 700; color: var(--navy); line-height: 1.25; }
.sc-path { font-size: 0.72rem; color: var(--muted); word-break: break-all; }
.sc-badges { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 0.35rem; }
.badge {
    font-size: 0.68rem; font-weight: 700; border-radius: 5px; padding: 0.1rem 0.45rem;
    background: var(--lavender); color: var(--primary);
}
.badge-muted { background: #F1F1F8; color: #49456B; }
.sc-quote {
    background: #fff; border-left: 3px solid var(--primary); border-radius: 4px;
    padding: 0.55rem 0.7rem; font-size: 0.8rem; color: #49456B; line-height: 1.45;
    font-style: italic;
}
.empty-state { text-align: center; color: var(--muted); font-size: 0.84rem; padding: 1.6rem 0.6rem; }
.empty-state .big { font-size: 1.8rem; margin-bottom: 0.4rem; }

/* ------------------------------------------------- Library / KB / History */
[class*="st-key-row_"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 0.95rem;
    box-shadow: var(--shadow);
}
[class*="st-key-row_"]:hover { border-color: #CDBEFD; }
.row-title { font-weight: 700; color: var(--navy); font-size: 0.93rem; line-height: 1.3; }
.row-sub { color: var(--muted); font-size: 0.8rem; margin-top: 2px; }
.row-meta { color: #9189B8; font-size: 0.74rem; margin-top: 4px; }

[class*="st-key-cat_"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1rem 0.6rem 1rem;
    box-shadow: var(--shadow);
    height: 100%;
}
.cat-name { font-weight: 700; color: var(--navy); font-size: 0.98rem; }
.cat-count { color: var(--muted); font-size: 0.78rem; margin-bottom: 0.4rem; }

.stat {
    background: var(--white); border: 1px solid var(--border); border-radius: 14px;
    padding: 1rem 1.15rem; box-shadow: var(--shadow); height: 100%;
}
.stat .v { font-size: 1.9rem; font-weight: 800; color: var(--primary); line-height: 1.1; }
.stat .l { font-size: 0.86rem; font-weight: 600; color: var(--navy); margin-top: 0.2rem; }
.stat .s { font-size: 0.74rem; color: var(--muted); margin-top: 0.15rem; }

/* --------------------------------------------------------- Responsive */
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; }
    .st-key-source_panel { position: static; }
}
@media (max-width: 640px) {
    .hero h1 { font-size: 1.6rem; }
    .hero p { font-size: 0.9rem; }
    [class*="st-key-msg_user_"] [data-testid="stChatMessage"] { max-width: 92%; }
    .st-key-quick_actions .stButton button { min-height: 92px; }
    .page-title { font-size: 1.2rem; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def esc(text: Any) -> str:
    return html.escape(str(text if text is not None else ""))


# -----------------------------------------------------------------------------
# DOCUMENT METADATA (REAL FILES ONLY)
# -----------------------------------------------------------------------------

# Explicit mapping for the repository's known documents.
_CATEGORY_BY_FILE = {
    "hr_policies.md": "HR & Company Policies",
    "it_onboarding.md": "IT Onboarding & Support",
    "troubleshooting.md": "Troubleshooting & FAQs",
    "company_overview.md": "Company Overview",
    "glossary.md": "Company Overview",
    "code_of_conduct.md": "Code of Conduct",
    "engineering_standards.md": "Engineering Standards",
    "development_workflow.md": "Engineering Standards",
    "technology_stack.md": "Technologies & Infrastructure",
    "current_projects.md": "Projects & Architecture",
    "project_architecture.md": "Projects & Architecture",
}

CATEGORY_ORDER = [
    "HR & Company Policies",
    "IT Onboarding & Support",
    "Company Overview",
    "Code of Conduct",
    "Engineering Standards",
    "Technologies & Infrastructure",
    "Projects & Architecture",
    "Troubleshooting & FAQs",
    "Uncategorized",
]


def get_document_category(filename: str) -> str:
    """Category for a document; keyword fallback for newly uploaded files."""
    name = os.path.basename(filename or "").lower()
    if name in _CATEGORY_BY_FILE:
        return _CATEGORY_BY_FILE[name]
    rules = [
        (("hr", "leave", "benefit", "policy", "policies"), "HR & Company Policies"),
        (("onboarding", "vpn", "laptop", "support"), "IT Onboarding & Support"),
        (("troubleshoot", "faq"), "Troubleshooting & FAQs"),
        (("conduct", "ethics"), "Code of Conduct"),
        (("engineering", "workflow", "standard", "coding"), "Engineering Standards"),
        (("technology", "stack", "infra"), "Technologies & Infrastructure"),
        (("project", "architecture"), "Projects & Architecture"),
        (("overview", "company", "glossary"), "Company Overview"),
    ]
    for keywords, cat in rules:
        if any(k in name for k in keywords):
            return cat
    return "Uncategorized"


def short_title(title: str) -> str:
    """Drops the 'Company — ' prefix used in document H1s for compact display."""
    for sep in (" — ", " – ", " - "):
        if sep in title:
            return title.split(sep, 1)[1].strip()
    return title


def file_badge(filename: str) -> str:
    ext = Path(filename or "").suffix.lstrip(".").upper()
    return ext[:4] or "DOC"


@st.cache_data(ttl=30, show_spinner=False)
def list_documents() -> List[Dict[str, Any]]:
    """Real documents present in the knowledge directory (.md and .txt)."""
    raw_dir = Path(RAW_DOCS_DIR)
    if not raw_dir.exists():
        return []
    docs: List[Dict[str, Any]] = []
    for path in sorted(list(raw_dir.glob("*.md")) + list(raw_dir.glob("*.txt"))):
        try:
            stat = path.stat()
            text = path.read_text(encoding="utf-8", errors="replace")
            h1 = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), None)
            title = h1 or path.stem.replace("_", " ").title()
            docs.append({
                "filename": path.name,
                "title": title,
                "short_title": short_title(title),
                "category": get_document_category(path.name),
                "updated": datetime.fromtimestamp(stat.st_mtime),
                "size_kb": round(stat.st_size / 1024, 1),
                "words": len(text.split()),
            })
        except OSError:
            continue
    return docs


def read_document(filename: str) -> Optional[str]:
    """Reads a document from the knowledge directory (path-traversal safe)."""
    safe = os.path.basename(filename or "")
    path = Path(RAW_DOCS_DIR) / safe
    if safe and path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    return None


@st.cache_data(ttl=30, show_spinner=False)
def index_stats() -> Dict[str, Any]:
    """Chunk counts straight from the ChromaDB index. Never fabricated."""
    try:
        from src.retrieve import load_vectorstore

        data = load_vectorstore().get(include=["metadatas"])
        metas = data.get("metadatas") or []
        per_source = Counter((m or {}).get("source", "unknown") for m in metas)
        return {"ok": True, "chunks": len(data.get("ids", [])), "per_source": dict(per_source), "error": None}
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a status
        return {"ok": False, "chunks": 0, "per_source": {}, "error": str(exc)}


def load_eval_checkpoint() -> List[Dict[str, Any]]:
    """Loads results written by eval/run_evaluation.py, if present."""
    path = Path(BASE_DIR) / "eval" / "results_checkpoint.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


# -----------------------------------------------------------------------------
# REUSABLE RENDERERS
# -----------------------------------------------------------------------------

ROUTE_LABELS = {
    "rag": "Knowledge base",
    "direct": "Direct answer",
    "clarify": "Needs clarification",
    "tool_calculator": "Calculator",
    "error": "Error",
}


def route_badge_html(route: Optional[str]) -> str:
    r = route if route in ROUTE_LABELS else "rag"
    return f'<span class="route route-{r}">{esc(ROUTE_LABELS[r])}</span>'


def source_chips_html(source_details: List[Dict[str, Any]]) -> str:
    chips = []
    for i, src in enumerate(source_details, start=1):
        fname = src.get("source", "")
        chips.append(
            f'<div class="src-chip"><div class="ico">{esc(file_badge(fname))}</div>'
            f'<div><div class="t">{esc(short_title(src.get("title") or fname))}</div>'
            f'<div class="c">{esc(get_document_category(fname))}</div></div>'
            f'<span class="n">[{i}]</span></div>'
        )
    return f'<div class="src-chips">{"".join(chips)}</div>'


def source_card_header_html(src: Dict[str, Any], index: int) -> str:
    fname = src.get("source", "")
    badges = [f'<span class="badge">Source [{index}]</span>']
    if src.get("chunk_index") is not None:
        badges.append(f'<span class="badge badge-muted">Chunk {int(src["chunk_index"]) + 1}</span>')
    score = src.get("score")
    if isinstance(score, (int, float)) and score > 0:
        badges.append(f'<span class="badge badge-muted">Relevance {score:.2f}</span>')
    return (
        f'<div class="sc-head"><div class="ico">{esc(file_badge(fname))}</div><div>'
        f'<div class="sc-title">{esc(short_title(src.get("title") or fname))}</div>'
        f'<div class="sc-path">{esc(get_document_category(fname))} / {esc(fname)}</div>'
        f'<div class="sc-badges">{"".join(badges)}</div></div></div>'
    )


def excerpt_html(text: str, limit: int = 260) -> str:
    t = " ".join((text or "").split())
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0] + "…"
    return f'<div class="sc-quote">“{esc(t)}”</div>'


def search_documents_and_threads(
    query: str,
    documents: List[Dict[str, Any]],
    conversations: Dict[str, Any],
) -> Dict[str, Any]:
    """Searches across document metadata, document text content, and conversation history."""
    q_low = query.strip().lower()
    if not q_low:
        return {"docs": [], "threads": []}

    # 1. Match documents
    matched_docs = []
    for d in documents:
        score = 0
        if q_low in d["title"].lower():
            score += 12
        if q_low in d["filename"].lower():
            score += 10
        if q_low in d["category"].lower():
            score += 6

        # Check full text content
        content = read_document(d["filename"]) or ""
        snippet = ""
        if q_low in content.lower():
            score += 4
            pos = content.lower().find(q_low)
            start = max(0, pos - 50)
            end = min(len(content), pos + 130)
            snippet = content[start:end].strip().replace("\n", " ")

        if score > 0:
            matched_docs.append({
                **d,
                "match_score": score,
                "snippet": snippet,
            })

    matched_docs.sort(key=lambda x: x["match_score"], reverse=True)

    # 2. Match conversation threads
    matched_threads = []
    for cid, c in conversations.items():
        t_score = 0
        if q_low in c.get("title", "").lower():
            t_score += 10
        for m in c.get("messages", []):
            if q_low in m.get("content", "").lower():
                t_score += 5
                break
        if t_score > 0:
            matched_threads.append(c)

    return {"docs": matched_docs, "threads": matched_threads}

