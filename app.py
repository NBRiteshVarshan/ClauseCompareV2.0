import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import html
import time

from document_processor import ClauseExtractor, get_document_summary
from clause_matcher import LegalClauseMatcher
from utils import format_report, save_report, generate_pdf_report, categorize_results
from db_manager import DatabaseManager

st.set_page_config(
    page_title="ClauseCompare V2.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Static CSS – safe (no user data)
st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; text-align: center; margin-bottom: 2rem; }
    .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center; }
    .stButton > button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }
    .stButton > button:hover { background-color: #1E40AF; color: white; }
    .doc-card { background-color: #F9FAFB; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid #3B82F6; position: relative; }
    .doc-card .status { font-size: 0.8rem; padding: 0.2rem 0.5rem; border-radius: 1rem; }
    .status-compared { background-color: #D1FAE5; color: #065F46; }
    .status-pending { background-color: #FEF3C7; color: #92400E; }
    .exact-box { background-color: #F0FDF4; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid #059669; }
    .partial-box { background-color: #FEF3C7; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid #D97706; }
    .unique-box { background-color: #FEF2F2; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid #DC2626; }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    if 'page' not in st.session_state:
        st.session_state.page = 'Dashboard'
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = None
    if 'compare_doc1_id' not in st.session_state:
        st.session_state.compare_doc1_id = None
    if 'compare_doc2_id' not in st.session_state:
        st.session_state.compare_doc2_id = None
    if 'compare_doc1_clauses' not in st.session_state:
        st.session_state.compare_doc1_clauses = None
    if 'compare_doc2_clauses' not in st.session_state:
        st.session_state.compare_doc2_clauses = None
    if 'confirm_delete_id' not in st.session_state:
        st.session_state.confirm_delete_id = None

def escape_text(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    return html.escape(text)

def main():
    init_session_state()
    db = st.session_state.db

    with st.sidebar:
        st.title("📂 ClauseCompare V2")
        st.caption("Your local contract management")
        st.divider()
        page = st.radio("Navigate", ["Dashboard", "Compare Documents", "Add Document", "Reports"])
        st.session_state.page = page
        st.divider()
        if st.button("🔄 Reset App", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            for key in list(st.session_state.keys()):
                if key != 'db':
                    del st.session_state[key]
            st.rerun()

    # ---------- DASHBOARD ----------
    if st.session_state.page == "Dashboard":
        st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
        stats = db.get_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="stats-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <h3>{stats['total']}</h3>
                    <p>Total Documents</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="stats-card" style="background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);">
                    <h3>{stats['compared']}</h3>
                    <p>Compared</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="stats-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <h3>{stats['pending']}</h3>
                    <p>Pending</p>
                </div>
            """, unsafe_allow_html=True)

        # Delete confirmation
        if st.session_state.confirm_delete_id:
            with st.expander("⚠️ Confirm Delete", expanded=True):
                doc = db.get_document(st.session_state.confirm_delete_id)
                if doc:
                    st.warning(f"Are you sure you want to delete '{doc['name']}'? This cannot be undone.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Delete", use_container_width=True):
                            db.delete_document(st.session_state.confirm_delete_id)
                            st.session_state.confirm_delete_id = None
                            st.success("Document deleted.")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", use_container_width=True):
                            st.session_state.confirm_delete_id = None
                            st.rerun()
                else:
                    st.session_state.confirm_delete_id = None
                    st.rerun()

        st.subheader("📄 Company Documents")
        company_docs = db.get_all_documents('company')
        if not company_docs:
            st.info("No company documents uploaded yet.")
        else:
            for doc in company_docs:
                status = "✅ Compared" if doc['is_compared'] else "⏳ Pending"
                col1, col2, col3 = st.columns([6, 2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="doc-card">
                            <strong>{doc['name']}</strong>
                            <span class="status {'status-compared' if doc['is_compared'] else 'status-pending'}">{status}</span>
                            <span style="float:right; color:#6B7280; font-size:0.8rem;">Uploaded: {doc['uploaded_at']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️", key=f"del_{doc['id']}"):
                        st.session_state.confirm_delete_id = doc['id']
                        st.rerun()

        st.subheader("📄 Third‑Party Documents")
        third_party_docs = db.get_all_documents('third_party')
        if not third_party_docs:
            st.info("No third‑party documents uploaded yet.")
        else:
            for doc in third_party_docs:
                status = "✅ Compared" if doc['is_compared'] else "⏳ Pending"
                col1, col2, col3 = st.columns([6, 2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="doc-card">
                            <strong>{doc['name']}</strong>
                            <span class="status {'status-compared' if doc['is_compared'] else 'status-pending'}">{status}</span>
                            <span style="float:right; color:#6B7280; font-size:0.8rem;">Uploaded: {doc['uploaded_at']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️", key=f"del_{doc['id']}"):
                        st.session_state.confirm_delete_id = doc['id']
                        st.rerun()

    # ---------- ADD DOCUMENT ----------
    elif st.session_state.page == "Add Document":
        st.markdown('<h1 class="main-header">📤 Add New Document</h1>', unsafe_allow_html=True)
        with st.form("upload_form"):
            doc_name = st.text_input("Document Name (optional)", placeholder="e.g., NDA_v3")
            category = st.selectbox("Category", ["company", "third_party"])
            uploaded_file = st.file_uploader("Upload PDF or DOCX", type=['pdf', 'docx'])
            submitted = st.form_submit_button("Upload & Extract")
            if submitted and uploaded_file is not None:
                with st.spinner("Extracting clauses..."):
                    extractor = ClauseExtractor()
                    try:
                        file_bytes = uploaded_file.read()
                        if uploaded_file.type == 'application/pdf':
                            clauses = extractor.extract_from_pdf(file_bytes)
                        else:
                            clauses = extractor.extract_from_docx(file_bytes)
                        doc_id = db.add_document(doc_name or uploaded_file.name, category)
                        db.add_clauses(doc_id, clauses)
                        st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully with {len(clauses)} clauses!")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ---------- COMPARE DOCUMENTS ----------
    elif st.session_state.page == "Compare Documents":
        st.markdown('<h1 class="main-header">⚖️ Compare Documents</h1>', unsafe_allow_html=True)

        company_docs = db.get_all_documents('company')
        third_party_docs = db.get_all_documents('third_party')

        if len(company_docs) < 1 or len(third_party_docs) < 1:
            st.warning("You need at least one Company document and one Third‑Party document to compare.")
        else:
            comp_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in company_docs}
            third_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in third_party_docs}

            col1, col2 = st.columns(2)
            with col1:
                selected1 = st.selectbox("📄 Select Company Document", options=list(comp_options.keys()))
                doc1_id = comp_options[selected1]
            with col2:
                selected2 = st.selectbox("📄 Select Third‑Party Document", options=list(third_options.keys()))
                doc2_id = third_options[selected2]

            # Comparison name input
            comparison_name = st.text_input(
                "✏️ Name this comparison (optional)",
                placeholder="e.g., NDA v3 vs Vendor A",
                help="Give this comparison a meaningful name for easy reference in the Reports section."
            )

            if st.button("🔄 Run Comparison", use_container_width=True):
                with st.spinner("Loading clauses and comparing..."):
                    clauses1 = db.get_clauses(doc1_id)
                    clauses2 = db.get_clauses(doc2_id)
                    if not clauses1 or not clauses2:
                        st.error("One of the documents has no clauses. Please re‑upload.")
                    else:
                        st.session_state.compare_doc1_id = doc1_id
                        st.session_state.compare_doc2_id = doc2_id
                        st.session_state.compare_doc1_clauses = clauses1
                        st.session_state.compare_doc2_clauses = clauses2

                        doc1 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses1]
                        doc2 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses2]

                        matcher = LegalClauseMatcher()
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()
                        def update_progress(prog, status):
                            progress_placeholder.progress(prog)
                            status_placeholder.text(status)

                        results = matcher.match_documents(
                            doc1, doc2,
                            similarity_threshold=0.4,
                            high_similarity_threshold=0.85,
                            match_threshold=0.5,
                            progress_callback=update_progress
                        )
                        result_id = db.save_comparison_result(doc1_id, doc2_id, results, comparison_name)
                        db.update_document_compared(doc1_id, result_id)
                        db.update_document_compared(doc2_id, result_id)
                        st.session_state.comparison_results = results
                        st.success("✅ Comparison complete! See results below.")
                        st.rerun()

            # Display results if they exist
            if st.session_state.comparison_results is not None:
                results = st.session_state.comparison_results
                clauses1 = st.session_state.compare_doc1_clauses
                clauses2 = st.session_state.compare_doc2_clauses
                if clauses1 is not None and clauses2 is not None:
                    doc1 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses1]
                    doc2 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses2]
                else:
                    doc1_id = st.session_state.compare_doc1_id
                    doc2_id = st.session_state.compare_doc2_id
                    if doc1_id and doc2_id:
                        clauses1 = db.get_clauses(doc1_id)
                        clauses2 = db.get_clauses(doc2_id)
                        if clauses1 and clauses2:
                            doc1 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses1]
                            doc2 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses2]
                        else:
                            doc1 = doc2 = []
                    else:
                        doc1 = doc2 = []

                if doc1 and doc2:
                    st.subheader("📊 Comparison Results")

                    # Coloured boxes for categories
                    exact, partial, unique = categorize_results(results, doc1, doc2)
                    total_matched = len(exact) + len(partial)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Clauses", len(doc1) + len(doc2))
                    col2.metric("Matched", total_matched)
                    col3.metric("Unique", len(unique))

                    with st.expander(f"✅ Exact Matches (Similarity ≥ 0.999) — {len(exact)} pairs"):
                        if exact:
                            for m in exact:
                                safe_doc1 = escape_text(m['doc1_text'])
                                safe_doc2 = escape_text(m['doc2_text'])
                                st.markdown(f"""
                                    <div class="exact-box">
                                        <strong>📄 Doc1 – Clause {m['doc1_num']}</strong><br>{safe_doc1}<br><br>
                                        <strong>📄 Doc2 – Clause {m['doc2_num']}</strong><br>{safe_doc2}<br><br>
                                        <span style="color:#059669;">✅ Similarity: {m['similarity']:.3f}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No exact matches found.")

                    with st.expander(f"🟡 Partial Matches (0.5 ≤ Similarity < 0.999) — {len(partial)} pairs"):
                        if partial:
                            for m in partial:
                                safe_doc1 = escape_text(m['doc1_text'])
                                safe_doc2 = escape_text(m['doc2_text'])
                                st.markdown(f"""
                                    <div class="partial-box">
                                        <strong>📄 Doc1 – Clause {m['doc1_num']}</strong><br>{safe_doc1}<br><br>
                                        <strong>📄 Doc2 – Clause {m['doc2_num']}</strong><br>{safe_doc2}<br><br>
                                        <span style="color:#D97706;">🔶 Similarity: {m['similarity']:.3f}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No partial matches found.")

                    with st.expander(f"🔴 Unique Clauses (not matched) — {len(unique)} clauses"):
                        if unique:
                            unique_doc1_list = [u for u in unique if u['document'] == 'Document 1']
                            unique_doc2_list = [u for u in unique if u['document'] == 'Document 2']
                            if unique_doc1_list:
                                st.markdown("**Document 1 Unique:**")
                                for u in unique_doc1_list:
                                    safe_text = escape_text(u['text'])
                                    st.markdown(f"""
                                        <div class="unique-box">
                                            <strong>Clause {u['number']}</strong><br>{safe_text}<br>
                                            <span style="color:#DC2626;">❌ Best similarity: {u['similarity']:.3f}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                            if unique_doc2_list:
                                st.markdown("**Document 2 Unique:**")
                                for u in unique_doc2_list:
                                    safe_text = escape_text(u['text'])
                                    st.markdown(f"""
                                        <div class="unique-box">
                                            <strong>Clause {u['number']}</strong><br>{safe_text}<br>
                                            <span style="color:#DC2626;">❌ Best similarity: {u['similarity']:.3f}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info("All clauses are matched (no unique clauses).")

                    st.subheader("📥 Download Reports")
                    txt_report = format_report(results)
                    json_report = save_report(results)
                    pdf_report = generate_pdf_report(results, doc1, doc2)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button("📄 PDF Report", pdf_report, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
                    with col2:
                        st.download_button("📄 TXT Report", txt_report, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    with col3:
                        st.download_button("📊 JSON Report", json_report, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    # ---------- REPORTS ----------
    elif st.session_state.page == "Reports":
        st.markdown('<h1 class="main-header">📜 Past Comparisons</h1>', unsafe_allow_html=True)
        comparisons = db.get_all_comparisons()
        if not comparisons:
            st.info("No past comparisons yet.")
        else:
            for comp in comparisons:
                display_name = comp['comparison_name'] if comp['comparison_name'] else f"Comparison #{comp['id']}"
                with st.expander(f"{display_name} – {comp['doc1_name']} vs {comp['doc2_name']} ({comp['timestamp']})"):
                    full = db.get_comparison_with_docs(comp['id'])
                    if full:
                        result_json = full['result_json']
                        clauses1 = db.get_clauses(full['doc1_id'])
                        clauses2 = db.get_clauses(full['doc2_id'])
                        doc1 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses1]
                        doc2 = [{'number': c['clause_number'], 'text': c['text'], 'metadata': c['metadata']} for c in clauses2]
                        if doc1 and doc2:
                            txt_report = format_report(result_json)
                            json_report = save_report(result_json)
                            pdf_report = generate_pdf_report(result_json, doc1, doc2)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button("📄 PDF", pdf_report, file_name=f"comparison_{comp['id']}.pdf", mime="application/pdf")
                            with col2:
                                st.download_button("📄 TXT", txt_report, file_name=f"comparison_{comp['id']}.txt")
                            with col3:
                                st.download_button("📊 JSON", json_report, file_name=f"comparison_{comp['id']}.json")
                        else:
                            st.warning("Could not retrieve clauses for this comparison.")
                    else:
                        st.warning("Could not load comparison data.")

if __name__ == "__main__":
    try:
        import ollama
        ollama.list()
    except Exception:
        st.warning("⚠️ Ollama not detected. Please start Ollama and pull llama3.2:3b.")
        st.info("""
        To install:
        1. Download Ollama from https://ollama.ai
        2. Run in terminal: `ollama pull llama3.2:3b`
        3. Run in terminal: `ollama serve`
        """)
    main()