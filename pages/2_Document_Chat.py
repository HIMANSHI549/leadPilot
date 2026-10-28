from pathlib import Path

import streamlit as st

from src.config import ROOT_DIR
from src.llm_service import LLMError
from src.memory_service import save_message
from src.rag_service import answer_question, ingest_pdf, list_documents
from src.ui import bootstrap

bootstrap()

st.title("Chat with Documents")
st.caption("Upload a PDF, store embeddings in PostgreSQL, and ask questions with source citations.")

sample_pdf = ROOT_DIR / "data" / "sample_company_profile.pdf"
uploads_dir = ROOT_DIR / "uploads"
uploads_dir.mkdir(exist_ok=True)

st.subheader("Upload a PDF")
uploaded = st.file_uploader("Choose a PDF", type=["pdf"])
if uploaded is not None:
    saved_path = uploads_dir / uploaded.name
    saved_path.write_bytes(uploaded.getbuffer())
    if st.button("Ingest this PDF"):
        with st.spinner("Extracting text, chunking, and creating embeddings..."):
            try:
                result = ingest_pdf(saved_path, filename=uploaded.name)
                st.success(
                    f"Stored {result['chunk_count']} chunks from {result['document']['filename']}."
                )
            except (ValueError, LLMError) as exc:
                st.error(str(exc))

if sample_pdf.exists():
    if st.button("Load the sample company PDF"):
        with st.spinner("Ingesting sample_company_profile.pdf..."):
            try:
                result = ingest_pdf(sample_pdf)
                st.success(f"Stored {result['chunk_count']} chunks from the sample PDF.")
            except (ValueError, LLMError) as exc:
                st.error(str(exc))

documents = list_documents()
st.subheader("Stored documents")
if not documents:
    st.info("No documents yet. Upload a PDF or load the sample file.")
else:
    st.dataframe(
        [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "chunks": doc["chunk_count"],
                "uploaded_at": doc["uploaded_at"],
            }
            for doc in documents
        ],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Ask a question")
question = st.text_input("Question about the uploaded documents")
if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving relevant chunks and generating an answer..."):
            try:
                result = answer_question(question)
                save_message("user", question, page="documents")
                save_message("assistant", result["answer"], page="documents")
                st.markdown(result["answer"])
                if result["sources"]:
                    st.markdown("**Sources**")
                    for index, source in enumerate(result["sources"], start=1):
                        with st.expander(
                            f"Source {index}: {source['filename']} (chunk {source['chunk_index']})"
                        ):
                            st.write(source["content"])
                            st.caption(f"Distance: {source['distance']:.4f}")
            except LLMError as exc:
                st.error(str(exc))
