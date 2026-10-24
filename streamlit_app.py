"""Company Knowledge Assistant — Minimal Agentic RAG Chatbot.

Focused, clean Streamlit chatbot demonstrating:
- Real-time RAG retrieval from ChromaDB
- LangGraph intent routing (RAG, Direct, Clarification, Calculator)
- Conversational memory with multi-turn follow-up resolution
- Verified source citations and honest abstention fallbacks
- Multiple isolated conversation threads with history switching & deletion
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from src.config import (
    BASE_DIR,
    RAW_DOCS_DIR,
    VECTORSTORE_DIR,
    validate_config,
)
from src.graph import build_graph
from src.ui_components import (
    inject_css,
    index_stats,
    list_documents,
    read_document,
    route_badge_html,
    source_chips_html,
    source_card_header_html,
    excerpt_html,
    short_title,
)

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Company Knowledge Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# -----------------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT (CONVERSATIONAL MEMORY)
# -----------------------------------------------------------------------------

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

if "conversations" not in st.session_state:
    init_id = "conv_default"
    st.session_state.conversations = {
        init_id: {
            "id": init_id,
            "title": "Welcome & Company Policies",
            "created_at": datetime.now(),
            "messages": [],
            "history": [],
        }
    }
    st.session_state.active_conv_id = init_id

if "active_conv_id" not in st.session_state or st.session_state.active_conv_id not in st.session_state.conversations:
    if st.session_state.conversations:
        st.session_state.active_conv_id = next(iter(st.session_state.conversations.keys()))
    else:
        new_id = f"conv_{int(datetime.now().timestamp())}"
        st.session_state.conversations[new_id] = {
            "id": new_id,
            "title": "New Conversation",
            "created_at": datetime.now(),
            "messages": [],
            "history": [],
        }
        st.session_state.active_conv_id = new_id

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


def get_current_conv() -> Dict[str, Any]:
    """Returns the currently active conversation dictionary."""
    cid = st.session_state.active_conv_id
    if cid not in st.session_state.conversations:
        st.session_state.conversations[cid] = {
            "id": cid,
            "title": "New Conversation",
            "created_at": datetime.now(),
            "messages": [],
            "history": [],
        }
    return st.session_state.conversations[cid]


# -----------------------------------------------------------------------------
# 3. DOCUMENT VIEWER DIALOG
# -----------------------------------------------------------------------------

@st.dialog("Document Viewer", width="large")
def show_document_dialog(filename: str):
    """Displays the full raw text of an approved internal document."""
    content = read_document(filename)
    if not content:
        st.error(f"Document '{filename}' could not be loaded from knowledge base.")
        return

    st.markdown(f"### 📄 `{filename}`")
    st.markdown("---")
    st.markdown(content)


# -----------------------------------------------------------------------------
# 4. QUERY PROCESSING (AGENTIC RAG PIPELINE)
# -----------------------------------------------------------------------------

def process_query(query_text: str):
    """Processes a user question through the LangGraph agent state machine."""
    clean_q = (query_text or "").strip()
    if not clean_q:
        return

    conv = get_current_conv()
    now_str = datetime.now().strftime("%I:%M %p")

    # Append user turn to UI messages
    conv["messages"].append({
        "role": "user",
        "content": clean_q,
        "timestamp": now_str,
    })

    # Auto-generate meaningful title from first question
    if conv["title"] in ("New Conversation", "Welcome & Company Policies") and len(conv["messages"]) == 1:
        conv["title"] = clean_q[:34] + ("…" if len(clean_q) > 34 else "")

    try:
        # Invoke LangGraph orchestrator with this conversation's isolated history
        result = st.session_state.graph.invoke({
            "question": clean_q,
            "route": None,
            "answer": None,
            "sources": None,
            "source_details": None,
            "history": conv["history"],  # Conversational memory passed to graph
            "is_grounded": None,
        })

        answer = result.get("answer") or "I couldn't find enough information to answer this question from the available company documentation."
        route = result.get("route", "rag")
        sources = result.get("sources", [])
        source_details = result.get("source_details", [])

        # Append assistant turn to UI messages
        conv["messages"].append({
            "role": "assistant",
            "content": answer,
            "route": route,
            "sources": sources,
            "source_details": source_details,
            "timestamp": now_str,
        })

        # Append to conversation's LangGraph turn history for multi-turn follow-ups
        conv["history"].append({
            "question": clean_q,
            "answer": answer,
            "route": route,
        })

    except Exception as exc:
        conv["messages"].append({
            "role": "assistant",
            "content": f"⚠️ An error occurred while retrieving or generating the response: {exc}",
            "route": "error",
            "sources": [],
            "source_details": [],
            "timestamp": now_str,
        })


# Handle pending query from suggested chips
if st.session_state.pending_query:
    pq = st.session_state.pending_query
    st.session_state.pending_query = None
    process_query(pq)
    st.rerun()


# -----------------------------------------------------------------------------
# 5. SIDEBAR (CONVERSATIONS & STATUS)
# -----------------------------------------------------------------------------

with st.sidebar:
    # Compact Brand Header
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-name">Knowledge Assistant</div>
                <div class="brand-sub">Aurelia Tech Documentation</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # + New Chat Action Button
    with st.container(key="new_chat"):
        if st.button("＋ New Chat", use_container_width=True):
            new_cid = f"conv_{int(datetime.now().timestamp())}"
            st.session_state.conversations[new_cid] = {
                "id": new_cid,
                "title": "New Conversation",
                "created_at": datetime.now(),
                "messages": [],
                "history": [],
            }
            st.session_state.active_conv_id = new_cid
            st.rerun()

    st.markdown('<div class="side-label">Previous Conversations</div>', unsafe_allow_html=True)

    # Render Conversation Threads List
    conv_items = list(st.session_state.conversations.values())
    conv_items.sort(key=lambda c: c.get("created_at") or datetime.min, reverse=True)

    for c in conv_items:
        c_id = c["id"]
        is_active = (c_id == st.session_state.active_conv_id)
        msg_count = len(c.get("messages", []))

        col_t, col_del = st.columns([8, 2])
        with col_t:
            btn_kind = "secondary" if is_active else "tertiary"
            label = f"💬 {c['title']}"
            if st.button(label, key=f"sel_{c_id}", type=btn_kind, use_container_width=True):
                st.session_state.active_conv_id = c_id
                st.rerun()

        with col_del:
            if st.button("🗑️", key=f"del_{c_id}", help="Delete this conversation", use_container_width=True):
                del st.session_state.conversations[c_id]
                # If deleted active, fallback to next available
                if st.session_state.active_conv_id == c_id:
                    if st.session_state.conversations:
                        st.session_state.active_conv_id = next(iter(st.session_state.conversations.keys()))
                    else:
                        fallback_id = f"conv_{int(datetime.now().timestamp())}"
                        st.session_state.conversations[fallback_id] = {
                            "id": fallback_id,
                            "title": "New Conversation",
                            "created_at": datetime.now(),
                            "messages": [],
                            "history": [],
                        }
                        st.session_state.active_conv_id = fallback_id
                st.rerun()

    # Small Real Knowledge Base Status
    stats = index_stats()
    doc_count = len(list_documents())
    dot_cls = "dot-ok" if stats["ok"] else "dot-bad"
    status_txt = f"{stats['chunks']} chunks across {doc_count} docs" if stats["ok"] else "Vectorstore Offline"

    st.markdown(
        f"""
        <div class="side-status">
            <span class="dot {dot_cls}"></span>
            <strong>Knowledge Base</strong><br/>
            {status_txt}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 6. MAIN CHAT AREA
# -----------------------------------------------------------------------------

# Main Top Header
stats_meta = index_stats()
status_indicator = "🟢 Vector DB Active" if stats_meta["ok"] else "🔴 Offline"

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 1.2rem; border-bottom: 1px solid var(--border); margin-bottom: 1.4rem;">
        <div>
            <h1 class="page-title" style="margin: 0; font-size: 1.6rem;">Company Knowledge Assistant</h1>
            <p class="page-sub" style="margin: 0.2rem 0 0 0;">Ask questions about company documentation.</p>
        </div>
        <div style="font-size: 0.8rem; font-weight: 600; color: var(--muted); background: var(--lavender); padding: 0.35rem 0.75rem; border-radius: 999px; border: 1px solid var(--border);">
            {status_indicator} · {stats_meta['chunks']} chunks
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

current_conv = get_current_conv()
messages = current_conv["messages"]

# Welcome screen with suggested questions if conversation has no messages
if len(messages) == 0:
    st.markdown(
        """
        <div class="hero" style="text-align: left; padding: 1.2rem 0;">
            <h2 style="font-size: 1.4rem; color: var(--navy); margin-bottom: 0.4rem;">
                👋 Welcome! How can I help you today?
            </h2>
            <p style="color: var(--muted); font-size: 0.95rem; margin-bottom: 1.2rem;">
                I am your internal AI assistant, grounded in verified documentation. Here are a few questions you can ask:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Suggested Question Prompt Chips
    sc1, sc2 = st.columns(2)
    with sc1:
        q1 = "📄 **What is our company's annual leave and sick leave policy?**"
        if st.button(q1, key="chip_leave", use_container_width=True):
            st.session_state.pending_query = "What is our company's annual leave and sick leave policy?"
            st.rerun()

        q2 = "💻 **How do I connect to the company VPN?**"
        if st.button(q2, key="chip_vpn", use_container_width=True):
            st.session_state.pending_query = "How do I connect to the company VPN?"
            st.rerun()

    with sc2:
        q3 = "🛠️ **What are our engineering standards for code reviews and PRs?**"
        if st.button(q3, key="chip_pr", use_container_width=True):
            st.session_state.pending_query = "What are our engineering standards for pull requests and code reviews?"
            st.rerun()

        q4 = "📜 **Summarize the key principles in our Code of Conduct.**"
        if st.button(q4, key="chip_conduct", use_container_width=True):
            st.session_state.pending_query = "Summarize the key principles in our Code of Conduct."
            st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)


# Render Conversation Message Stream
for idx, msg in enumerate(messages):
    role = msg["role"]
    if role == "user":
        with st.container(key=f"msg_user_{idx}"):
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
                t_str = msg.get("timestamp")
                if t_str:
                    st.markdown(f'<div class="msg-time">{t_str}</div>', unsafe_allow_html=True)
    else:
        with st.container(key=f"msg_asst_{idx}"):
            with st.chat_message("assistant", avatar="✨"):
                # Unobtrusive Route Badge
                route = msg.get("route", "rag")
                st.markdown(route_badge_html(route), unsafe_allow_html=True)

                # Formatted Answer Text
                st.markdown(msg["content"])

                # Verified Source Citations Section
                source_details = msg.get("source_details", [])
                if source_details:
                    # Clean inline source chips
                    st.markdown(source_chips_html(source_details), unsafe_allow_html=True)

                    # Expandable details with quoted excerpts
                    exp_label = f"📚 Sources ({len(source_details)} document{'s' if len(source_details) > 1 else ''})"
                    with st.expander(exp_label):
                        for s_i, src in enumerate(source_details, start=1):
                            st.markdown(source_card_header_html(src, s_i), unsafe_allow_html=True)
                            excerpt = src.get("excerpt", "")
                            if excerpt:
                                st.markdown(excerpt_html(excerpt), unsafe_allow_html=True)

                            src_file = src.get("source", "")
                            if src_file and st.button(f"📖 View '{src_file}'", key=f"view_src_{idx}_{s_i}"):
                                show_document_dialog(src_file)


# -----------------------------------------------------------------------------
# 7. CHAT INPUT COMPOSER
# -----------------------------------------------------------------------------

user_input = st.chat_input("Ask a question about company documentation...")

if user_input:
    with st.spinner("Searching company documentation & generating answer..."):
        process_query(user_input)
    st.rerun()