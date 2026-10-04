"""Streamlit user interface for StudyMate."""
from pathlib import Path
import os
import streamlit as st
from src.study_mate import answer_question, citation_label, load_local_env, load_notes

ROOT = Path(__file__).parent
load_local_env(ROOT)
st.set_page_config(page_title="StudyMate", page_icon="📚")
st.title("StudyMate")
st.caption("Ask questions about course notes and inspect the retrieved sources.")
chunks = load_notes(ROOT / "data" / "public_pdfs")
question = st.text_input("Ask a question about the supplied notes", placeholder="What is retrieval augmented generation?")
use_llm = st.checkbox("Use hosted LLM (OpenAI or OpenRouter key required)", value=False)
if st.button("Answer", type="primary") and question:
    if use_llm and not (os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')):
        st.error('Configure an OpenAI or OpenRouter API key to use hosted mode.')
        st.stop()
    try:
        result = answer_question(question, chunks, use_llm=use_llm)
    except Exception:
        st.error('The request could not be completed. Check your configuration, connection and source files. This is an operational error, not an evidence refusal.')
        st.stop()
    if result.refused:
        st.warning("not found")
        st.caption("The question was outside the allowed scope or the system did not find sufficient evidence to answer.")
    else:
        st.write(result.answer)
        st.caption(f"Sources: {citation_label(result)} · Retrieval score: {result.score:.2f} · Mode: {result.mode}")
        with st.expander("Inspect retrieved evidence"):
            st.caption("These are retrieved candidates, not verified claim-level citations.")
            for chunk in result.citations:
                st.markdown(f"**{chunk.source}, page {chunk.page}**")
                st.text(chunk.text)
st.divider()
st.caption("Intended use: study support only. Do not use for grading, personal-data queries or professional advice.")
