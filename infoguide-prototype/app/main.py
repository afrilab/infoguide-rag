import streamlit as st
from ingestion import save_uploaded_file, extract_text
from preprocessing import preprocess_text
from chunking import (
    chunk_text,
    save_chunks
)
from embeddings import (
    MODEL_NAME as BGE_MODEL_NAME,
    load_bge_model,
    load_chunks,
    create_embeddings_batch,
    save_embeddings
)

from query_processing import (
    GPT_MODEL_NAME,
    load_gpt_client,
    expand_query_with_gpt,
    decompose_query_with_gpt,
    create_query_embedding,
    create_sub_query_embeddings,
)

from retrieval import (
    load_embeddings_and_metadata,
    build_faiss_index,
    retrieve_with_faiss,
    build_bm25_index,
    retrieve_with_bm25,
    retrieve_hybrid,
    retrieve_multi_query,
)
from generation import generate_answer_with_gpt
from reranking import load_reranker_model, rerank_results
from image_description import (
    VISION_MODEL,
    load_vision_client,
    collect_images,
    run_image_description,
    IMAGES_DIR,
)
import webbrowser
from pathlib import Path

RAW_DATA_DIR = Path("data/raw")


def show_chunk_source(chunk, key_suffix=""):
    metadata = chunk.get("metadata", {})
    chunk_type = metadata.get("chunk_type", "chunk")

    if chunk_type == "image_description":
        image_path = metadata.get("image_path")
        if image_path:
            img_path = Path(image_path)
            if img_path.exists():
                st.caption(f"Source image: {img_path.name}")
                st.image(str(img_path), use_container_width=True)
            else:
                st.warning(f"Image file not found: {image_path}")
        else:
            st.caption("No image path in metadata.")
        return

    source_file = metadata.get("source_file")
    start_page = metadata.get("start_page")

    if not source_file:
        st.caption("No source file information in metadata.")
        return

    pdf_path = RAW_DATA_DIR / source_file
    if not pdf_path.exists():
        st.warning(f"Source file not found: {pdf_path}")
        return

    ext = source_file.rsplit(".", 1)[-1].lower() if "." in source_file else ""
    page_label = f"· Page {start_page}" if start_page else ""
    st.caption(f"📄 {source_file}{page_label}")

    if st.button("Open in local viewer", key=f"open_pdf_{key_suffix}"):
        if ext == "pdf":
            import tempfile, threading, time, os
            import fitz

            chunk_text = chunk.get("text", "")
            marker = "Content:\n"
            idx = chunk_text.find(marker)
            content_text = chunk_text[idx + len(marker):].strip() if idx != -1 else chunk_text.strip()
            end_page = metadata.get("end_page") or start_page

            def _open_with_highlight():
                tmp_pdf_path = None
                tmp_html_path = None
                try:
                    doc = fitz.open(str(pdf_path.resolve()))
                    heading_text = metadata.get("heading", "")
                    if start_page:
                        for pg_num in range(start_page, min((end_page or start_page) + 1, len(doc) + 1)):
                            page = doc[pg_num - 1]
                            search_lines = []
                            if heading_text:
                                search_lines.append(heading_text)
                            search_lines.extend(
                                line.strip() for line in content_text.splitlines()
                                if len(line.strip()) > 15
                            )
                            for line in search_lines:
                                for inst in page.search_for(line):
                                    annot = page.add_highlight_annot(inst)
                                    annot.update()
                    f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    tmp_pdf_path = f.name
                    f.close()
                    doc.save(tmp_pdf_path)
                    doc.close()

                    uri = Path(tmp_pdf_path).as_uri()
                    if start_page:
                        uri += f"#page={start_page}"
                    f2 = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".html", delete=False, encoding="utf-8"
                    )
                    tmp_html_path = f2.name
                    f2.write(
                        f'<html><head><script>window.location="{uri}";</script></head><body></body></html>'
                    )
                    f2.close()
                    webbrowser.open(Path(tmp_html_path).as_uri())

                    time.sleep(15)
                finally:
                    for p in [tmp_pdf_path, tmp_html_path]:
                        if p:
                            try:
                                os.unlink(p)
                            except Exception:
                                pass

            threading.Thread(target=_open_with_highlight, daemon=True).start()
        else:
            import os
            os.startfile(str(pdf_path.resolve()))


st.set_page_config(
    page_title="InfoGuide",
    page_icon="📄",
    layout="wide"
)


st.markdown(
    """
    <style>
    :root {
        color-scheme: light !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .block-container,
    [data-testid="stMain"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    html, body, p, span, div, label,
    h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stText, .stTextInput, .stTextArea {
        color: #000000 !important;
    }

    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 6px !important;
    }

    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] * {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #000000 !important;
    }

    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploadDropzone"] button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
    }

    [data-testid="stFileUploader"] svg {
        fill: #000000 !important;
        color: #000000 !important;
    }

    textarea,
    input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }

    textarea:focus,
    input:focus {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #000000 !important;
        box-shadow: none !important;
    }

    .stAlert,
    .stAlert * {
        color: #000000 !important;
    }

    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 10px;
        color: #000000 !important;
    }

    .subtitle {
        font-size: 18px;
        color: #000000 !important;
        margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


if "page" not in st.session_state:
    st.session_state["page"] = "ingestion"


def show_ingestion_page():
    st.markdown(
        '<div class="main-title">InfoGuide RAG Pipeline</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 1: Upload one or more documents and run ingestion.</div>',
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) selected: {', '.join(f.name for f in uploaded_files)}")

        if st.button("Run Ingestion"):
            extracted_texts = []
            progress_bar = st.progress(0)
            all_succeeded = True

            for i, uploaded_file in enumerate(uploaded_files, start=1):
                try:
                    file_path = save_uploaded_file(uploaded_file)
                    text = extract_text(file_path)
                    extracted_texts.append({"filename": uploaded_file.name, "text": text})
                    st.info(f"[{i}/{len(uploaded_files)}] Extracted: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Ingestion failed for {uploaded_file.name}: {e}")
                    all_succeeded = False
                progress_bar.progress(i / len(uploaded_files))

            if extracted_texts:
                st.session_state["extracted_texts"] = extracted_texts
                st.session_state["ingestion_done"] = True
                if all_succeeded:
                    st.success("Ingestion completed successfully.")

    if st.session_state.get("ingestion_done"):
        st.markdown("---")
        st.subheader("Extracted Text Preview")

        for item in st.session_state["extracted_texts"]:
            with st.expander(item["filename"]):
                st.text_area(
                    f"Preview — {item['filename']}",
                    item["text"],
                    height=200,
                    key=f"preview_{item['filename']}"
                )

        st.markdown("---")
        st.success("Step 1 completed: Ingestion")

        if st.button("Next Step: Preprocessing → Click to Continue"):
            st.session_state["page"] = "preprocessing"
            st.rerun()


def show_preprocessing_page():
    st.markdown(
        '<div class="main-title">Preprocessing</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 2: Clean and prepare the extracted texts before chunking.</div>',
        unsafe_allow_html=True
    )

    st.success("Ingestion data is ready.")

    st.subheader("Original Extracted Texts")
    for item in st.session_state.get("extracted_texts", []):
        with st.expander(item["filename"]):
            st.text_area(
                f"Original — {item['filename']}",
                item["text"],
                height=200,
                key=f"orig_{item['filename']}"
            )

    if st.button("Run Preprocessing"):
        try:
            extracted_texts = st.session_state.get("extracted_texts", [])
            preprocessed_texts = []
            all_logs = []

            for item in extracted_texts:
                preprocessed_text, logs = preprocess_text(item["text"])
                preprocessed_texts.append({"filename": item["filename"], "text": preprocessed_text})
                all_logs.extend(logs)

            st.session_state["preprocessed_texts"] = preprocessed_texts
            st.session_state["preprocessing_logs"] = all_logs
            st.session_state["preprocessing_done"] = True

            st.success(f"Preprocessing completed for {len(preprocessed_texts)} document(s).")

        except Exception as e:
            st.error(f"Preprocessing failed: {e}")

    if st.session_state.get("preprocessing_done"):
        st.subheader("Preprocessed Texts")
        for item in st.session_state["preprocessed_texts"]:
            with st.expander(item["filename"]):
                st.text_area(
                    f"Preprocessed — {item['filename']}",
                    item["text"],
                    height=200,
                    key=f"prep_{item['filename']}"
                )

        st.markdown("---")
        st.success("Step 2 completed: Preprocessing")

        if st.button("Continue to Chunking"):
            st.session_state["page"] = "chunking"
            st.rerun()


def show_chunking_page():
    st.markdown(
        '<div class="main-title">Chunking</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 3: Create document chunks with Recommended Chunking.</div>',
        unsafe_allow_html=True
    )

    st.success("Preprocessed text is ready.")

    st.subheader("Recommended Chunking")
    st.info(
        "Uses heading-aware recursive chunking with overlap and metadata."
    )

    st.markdown("---")

    if st.button("Start Chunking"):
        try:
            preprocessed_texts = st.session_state.get("preprocessed_texts", [])

            if not preprocessed_texts:
                st.warning("No preprocessed text found. Please complete preprocessing first.")
                return

            all_chunks = []
            all_logs = []
            chunk_id = 1

            with st.spinner("Chunking is running..."):
                for item in preprocessed_texts:
                    chunks, logs = chunk_text(item["text"])
                    for chunk in chunks:
                        chunk["chunk_id"] = chunk_id
                        chunk["metadata"]["source_file"] = item["filename"]
                        chunk_id += 1
                    all_chunks.extend(chunks)
                    all_logs.extend(logs)
                    st.info(f"Chunked: {item['filename']} → {len(chunks)} chunks")

                chunks_output_path = save_chunks(all_chunks)

            st.session_state["chunks"] = all_chunks
            st.session_state["chunking_logs"] = all_logs
            st.session_state["chunking_done"] = True
            st.session_state["chunks_output_path"] = str(chunks_output_path)

            st.success(f"Chunking finished. Total: {len(all_chunks)} chunks across {len(preprocessed_texts)} document(s).")

        except Exception as e:
            st.error(f"Chunking failed: {e}")

    if st.session_state.get("chunking_done"):
        st.markdown("---")
        st.success("Step 3 completed: Chunking is finished.")

        st.info(f"Chunks saved to: {st.session_state['chunks_output_path']}")

        chunks = st.session_state.get("chunks", [])

        st.subheader("Chunk Preview")

        for chunk in chunks[:5]:
            metadata = chunk.get("metadata", {})

            st.markdown(f"### Chunk {chunk['chunk_id']}")

            st.info(f"Heading: {metadata.get('heading', chunk.get('heading', '-'))}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.caption(f"Source: {metadata.get('source_file', '-')}")

            with col2:
                st.caption(f"Section index: {metadata.get('section_index', '-')}")

            with col3:
                st.caption(f"Sub-chunk: {metadata.get('sub_chunk_id', '-')}")

            with col4:
                st.caption(f"Characters: {chunk.get('char_count', '-')}")

            st.text_area(
                f"Chunk {chunk['chunk_id']}",
                chunk["text"],
                height=180
            )

        if len(chunks) > 5:
            st.info(f"Showing first 5 chunks out of {len(chunks)} total chunks.")

        if st.button("Continue to Embedding"):
            st.session_state["page"] = "embedding"
            st.rerun()
            
def show_embedding_page():
    st.markdown(
        '<div class="main-title">Embedding</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 4: Load BGE-M3 and create embeddings for chunks.</div>',
        unsafe_allow_html=True
    )

    st.success("Chunking is completed. Chunks are ready for embedding.")

    st.subheader("Selected Embedding Model")
    st.info(f"Model: {BGE_MODEL_NAME}")

    if st.button("Load BGE-M3 Model"):
        try:
            progress_text = st.empty()

            with st.spinner("Loading BGE-M3 model... This may take a while."):
                progress_text.info("Downloading / loading BGE-M3 model...")
                bge_model = load_bge_model()

            st.session_state["bge_model"] = bge_model
            st.session_state["bge_model_loaded"] = True

            progress_text.success("Done. BGE-M3 model loaded successfully.")

        except Exception as e:
            st.error(f"BGE-M3 model loading failed: {e}")

    if st.session_state.get("bge_model_loaded"):
        st.markdown("---")
        st.success("BGE-M3 model is ready.")

        if st.button("Create Embeddings"):
            try:
                chunks = load_chunks()
                bge_model = st.session_state["bge_model"]

                st.info(f"Total chunks found: {len(chunks)}")

                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current_chunk, total_chunks):
                    progress = current_chunk / total_chunks
                    progress_bar.progress(progress)
                    status_text.info(
                        f"Creating embedding for Chunk {current_chunk} / {total_chunks}"
                    )

                vectors = create_embeddings_batch(
                    chunks,
                    bge_model,
                    progress_callback=update_progress
                )

                embeddings_path, metadata_path = save_embeddings(chunks, vectors)

                st.session_state["embedding_done"] = True
                st.session_state["embeddings_path"] = str(embeddings_path)
                st.session_state["embedding_metadata_path"] = str(metadata_path)

                status_text.success("Embedding creation completed.")
                st.success("Step 4 completed: Embeddings created successfully.")

                st.info(f"Embeddings saved to: {embeddings_path}")
                st.info(f"Metadata saved to: {metadata_path}")

            except Exception as e:
                st.error(f"Embedding creation failed: {e}")

    if st.session_state.get("embedding_done"):
        st.markdown("---")
        st.success("Embedding step is finished.")
        st.info(f"Embeddings file: {st.session_state['embeddings_path']}")
        st.info(f"Metadata file: {st.session_state['embedding_metadata_path']}")

        if st.button("Continue to Image Description"):
            st.session_state["page"] = "image_description"
            st.rerun()
def show_image_description_page():
    st.markdown(
        '<div class="main-title">Image Description</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 5: Describe extracted images with GPT-4o Vision and add them as chunks.</div>',
        unsafe_allow_html=True
    )

    st.success("Embeddings are ready. Now we will describe any images extracted from the document.")

    images = collect_images(IMAGES_DIR)
    if not images:
        st.warning("No images found in data/images/. You can skip this step.")
        if st.button("Skip — Continue to Query Processing"):
            st.session_state["page"] = "query_expansion"
            st.rerun()
        return

    st.info(f"Found {len(images)} image(s). All will be described.")

    st.subheader("Vision Model")
    st.info(f"Model: {VISION_MODEL}")

    if st.button("Load GPT-4o Vision Client"):
        try:
            vision_client = load_vision_client()
            st.session_state["vision_client"] = vision_client
            st.session_state["vision_client_loaded"] = True
            st.success("GPT-4o Vision client loaded successfully.")
        except Exception as e:
            st.error(f"Failed to load vision client: {e}")

    if st.session_state.get("vision_client_loaded"):
        st.markdown("---")

        if "bge_model" not in st.session_state:
            st.warning("BGE-M3 model is not loaded. Please go back to the Embedding step and load the model first.")
            return

        if st.button("Describe All Images"):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current, total, filename):
                    progress_bar.progress(current / total)
                    status_text.info(f"Describing image {current}/{total}: {filename}")

                with st.spinner("Sending images to GPT-4o Vision..."):
                    image_chunks, logs = run_image_description(
                        client=st.session_state["vision_client"],
                        bge_model=st.session_state["bge_model"],
                        progress_callback=update_progress,
                    )

                st.session_state["image_chunks"] = image_chunks
                st.session_state["image_description_done"] = True

                status_text.empty()
                progress_bar.empty()

                for log in logs:
                    st.info(log)

                st.success(f"Image description completed. {len(image_chunks)} image chunk(s) added.")

            except Exception as e:
                st.error(f"Image description failed: {e}")

    if st.session_state.get("image_description_done"):
        st.markdown("---")

        image_chunks = st.session_state.get("image_chunks", [])

        if image_chunks:
            st.subheader("Image Chunk Preview")
            for chunk in image_chunks[:3]:
                meta = chunk.get("metadata", {})
                st.markdown(f"### Chunk {chunk['chunk_id']} — {chunk['heading']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Image path: {meta.get('image_path', '-')}")
                with col2:
                    st.caption(f"Page: {meta.get('page_number', '-')}")
                st.text_area(
                    f"Image Chunk {chunk['chunk_id']}",
                    chunk["text"],
                    height=180,
                )
            if len(image_chunks) > 3:
                st.info(f"Showing first 3 of {len(image_chunks)} image chunks.")

        st.success("Step 5 completed: Image Description")

        if st.button("Continue to Query Processing"):
            st.session_state["page"] = "query_expansion"
            st.rerun()


def show_query_expansion_page():
    st.markdown(
        '<div class="main-title">Query Expansion</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 6: Expand the query with GPT-4o mini and create query embedding.</div>',
        unsafe_allow_html=True
    )

    st.success("Embeddings are ready.")

    st.subheader("Query Expansion Model")
    st.info(f"Model: {GPT_MODEL_NAME}")

    if st.button("Load GPT-4o mini Client"):
        try:
            gpt_client = load_gpt_client()

            st.session_state["gpt_client"] = gpt_client
            st.session_state["gpt_loaded"] = True

            st.success("GPT-4o mini client loaded successfully.")

        except Exception as e:
            st.error(f"GPT client loading failed: {e}")

    if st.session_state.get("gpt_loaded"):
        query = st.text_input("Enter your query")

        if query:
            st.session_state["original_query"] = query

        if st.button("Expand Query"):
            try:
                original_query = st.session_state.get("original_query", "")

                if not original_query:
                    st.warning("Please enter a query first.")
                    return

                with st.spinner("Expanding query with GPT-4o mini..."):
                    full_output, expanded_query = expand_query_with_gpt(
                        original_query,
                        st.session_state["gpt_client"]
                    )
                    sub_queries = decompose_query_with_gpt(
                        original_query,
                        st.session_state["gpt_client"]
                    )

                st.session_state["gpt_full_output"] = full_output
                st.session_state["expanded_query"] = expanded_query
                st.session_state["sub_queries"] = sub_queries
                st.session_state["query_expanded"] = True

                st.success("Query expansion completed.")

            except Exception as e:
                st.error(f"Query expansion failed: {e}")

    if st.session_state.get("query_expanded"):
        st.markdown("---")

        st.subheader("Original Query")
        st.write(st.session_state["original_query"])

        st.subheader("GPT Output")
        st.text_area(
            "Expanded Query Details",
            st.session_state["gpt_full_output"],
            height=220
        )

        st.subheader("Final Expanded Query")
        st.text_area(
            "Expanded Query",
            st.session_state["expanded_query"],
            height=120
        )

        st.subheader("Sub-queries")
        for i, sq in enumerate(st.session_state.get("sub_queries", []), start=1):
            st.caption(f"{i}. {sq}")

        if st.button("Create Query Embedding"):
            try:
                expanded_query = st.session_state["expanded_query"]

                if "bge_model" not in st.session_state:
                    st.warning("BGE model is not loaded. Please go back to Embedding page.")
                    return

                with st.spinner("Creating query embeddings with BGE-M3..."):
                    query_vector = create_query_embedding(
                        expanded_query,
                        st.session_state["bge_model"]
                    )
                    sub_query_vectors = create_sub_query_embeddings(
                        st.session_state.get("sub_queries", [expanded_query]),
                        st.session_state["bge_model"]
                    )

                st.session_state["query_vector"] = query_vector
                st.session_state["sub_query_vectors"] = sub_query_vectors
                st.session_state["query_embedding_done"] = True

                st.success("Query embeddings created successfully.")
                st.info(f"Query vector shape: {query_vector.shape} — {len(sub_query_vectors)} sub-query vector(s)")

            except Exception as e:
                st.error(f"Query embedding creation failed: {e}")

    if st.session_state.get("query_embedding_done"):
        st.markdown("---")

        if st.button("Continue to Retrieval"):
            st.session_state["page"] = "retrieval"
            st.rerun()
def show_retrieval_page():
    st.markdown(
        '<div class="main-title">Retrieval</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 7: Retrieve relevant chunks using FAISS or BM25.</div>',
        unsafe_allow_html=True
    )

    if "expanded_query" not in st.session_state:
        st.warning("No expanded query found. Please complete query expansion first.")
        return

    if "query_vector" not in st.session_state:
        st.warning("No query embedding found. Please complete query embedding first.")
        return

    st.success("Expanded query and query embedding are ready.")

    st.subheader("Expanded Query")
    st.text_area(
        "Query used for retrieval",
        st.session_state["expanded_query"],
        height=120
    )

    st.markdown("---")

    st.subheader("Choose Retrieval Method")

    retrieval_method = st.radio(
        "Select retrieval method",
        ["Hybrid (FAISS + BM25)", "FAISS", "BM25"]
    )

    st.session_state["retrieval_method"] = retrieval_method

    top_k = st.number_input(
        "Top-K chunks to retrieve",
        min_value=1,
        max_value=20,
        value=5
    )

    if st.button("Build Retrieval Index"):
        try:
            embeddings, metadata = load_embeddings_and_metadata()
            st.session_state["retrieval_metadata"] = metadata

            if retrieval_method == "Hybrid (FAISS + BM25)":
                with st.spinner("Building FAISS + BM25 indexes..."):
                    faiss_index = build_faiss_index(embeddings)
                    bm25_index = build_bm25_index(metadata)
                st.session_state["faiss_index"] = faiss_index
                st.session_state["bm25_index"] = bm25_index
                st.session_state["index_built"] = True
                st.success("Hybrid index (FAISS + BM25) built successfully.")

            elif retrieval_method == "FAISS":
                with st.spinner("Building FAISS index..."):
                    faiss_index = build_faiss_index(embeddings)
                st.session_state["faiss_index"] = faiss_index
                st.session_state["index_built"] = True
                st.success("FAISS index built successfully.")

            else:
                with st.spinner("Building BM25 index..."):
                    bm25_index = build_bm25_index(metadata)
                st.session_state["bm25_index"] = bm25_index
                st.session_state["index_built"] = True
                st.success("BM25 index built successfully.")

        except Exception as e:
            st.error(f"Index building failed: {e}")

    if st.session_state.get("index_built"):
        if st.button("Run Retrieval"):
            try:
                metadata = st.session_state["retrieval_metadata"]
                original_query = st.session_state["original_query"]
                sub_query_vectors = st.session_state.get("sub_query_vectors", [st.session_state["query_vector"]])
                sub_queries_list = st.session_state.get("sub_queries", [original_query])

                if retrieval_method == "Hybrid (FAISS + BM25)":
                    results = retrieve_multi_query(
                        sub_query_vectors,
                        sub_queries_list,
                        st.session_state["faiss_index"],
                        st.session_state["bm25_index"],
                        metadata,
                        top_k=top_k,
                    )

                elif retrieval_method == "FAISS":
                    results = retrieve_multi_query(
                        sub_query_vectors,
                        sub_queries_list,
                        st.session_state["faiss_index"],
                        None,
                        metadata,
                        top_k=top_k,
                    )

                else:
                    results = retrieve_multi_query(
                        sub_query_vectors,
                        sub_queries_list,
                        None,
                        st.session_state["bm25_index"],
                        metadata,
                        top_k=top_k,
                    )

                st.session_state["retrieval_results"] = results
                st.session_state["retrieval_done"] = True

                st.success("Retrieval completed successfully.")

            except Exception as e:
                st.error(f"Retrieval failed: {e}")

    if st.session_state.get("retrieval_done"):
        st.markdown("---")
        st.subheader("Retrieved Chunks")

        results = st.session_state["retrieval_results"]

        for rank, result in enumerate(results, start=1):
            st.markdown(f"### Rank {rank} | Chunk {result['chunk_id']}")
            faiss_rank = result.get("faiss_rank")
            bm25_rank = result.get("bm25_rank")
            if faiss_rank is not None or bm25_rank is not None:
                label = f"RRF Score: {result['score']:.4f}  |  FAISS rank: {faiss_rank or '—'}  |  BM25 rank: {bm25_rank or '—'}"
                st.info(label)
            else:
                st.info(f"Score: {result['score']:.4f}")

            st.text_area(
                f"Retrieved Chunk {result['chunk_id']}",
                result["text"],
                height=220
            )

        st.markdown("---")
        st.subheader("Next Step")

        st.write("Do you want to apply reranking to the retrieved chunks?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes, continue to Reranking"):
                st.session_state["page"] = "reranking"
                st.rerun()

        with col2:
            if st.button("No, continue to Generation Response"):
                st.session_state["final_context_chunks"] = st.session_state["retrieval_results"]
                st.session_state["page"] = "generation"
                st.rerun()

def show_reranking_page():
    st.markdown(
        '<div class="main-title">Reranking</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 8: Rerank retrieved chunks using BGE reranker.</div>',
        unsafe_allow_html=True
    )

    if "retrieval_results" not in st.session_state:
        st.warning("No retrieval results found. Please complete retrieval first.")
        return

    st.success("Retrieved chunks are ready for reranking.")

    retrieved_results = st.session_state["retrieval_results"]

    st.subheader("Retrieved Chunks Before Reranking")

    for rank, result in enumerate(retrieved_results, start=1):
        st.markdown(f"### Original Rank {rank} | Chunk {result['chunk_id']}")
        st.info(f"Retrieval Score: {result['score']:.4f}")

        st.text_area(
            f"Before Reranking Chunk {result['chunk_id']}",
            result["text"],
            height=160
        )

    st.markdown("---")

    if st.button("Load Reranker Model"):
        try:
            with st.spinner("Loading BGE reranker model..."):
                reranker_model = load_reranker_model()

            st.session_state["reranker_model"] = reranker_model
            st.session_state["reranker_loaded"] = True

            st.success("Reranker model loaded successfully.")

        except Exception as e:
            st.error(f"Reranker model loading failed: {e}")

    if st.session_state.get("reranker_loaded"):
        rerank_top_k = st.number_input(
            "Top-K chunks after reranking",
            min_value=1,
            max_value=len(retrieved_results),
            value=min(5, len(retrieved_results))
        )

        if st.button("Run Reranking"):
            try:
                expanded_query = st.session_state["expanded_query"]

                with st.spinner("Reranking retrieved chunks..."):
                    reranked_results = rerank_results(
                        query=st.session_state["original_query"],
                        retrieved_results=retrieved_results,
                        reranker_model=st.session_state["reranker_model"],
                        top_k=rerank_top_k
                    )

                st.session_state["reranked_results"] = reranked_results
                st.session_state["final_context_chunks"] = reranked_results
                st.session_state["reranking_done"] = True

                st.success("Reranking completed successfully.")

            except Exception as e:
                st.error(f"Reranking failed: {e}")

    if st.session_state.get("reranking_done"):
        st.markdown("---")
        st.subheader("Reranked Chunks")

        for rank, result in enumerate(st.session_state["reranked_results"], start=1):
            st.markdown(f"### New Rank {rank} | Chunk {result['chunk_id']}")
            st.info(f"Rerank Score: {result['rerank_score']:.4f}")

            st.text_area(
                f"Reranked Chunk {result['chunk_id']}",
                result["text"],
                height=180
            )

        if st.button("Continue to Generation Response"):
            st.session_state["page"] = "generation"
            st.rerun()
def show_generation_page():
    st.markdown(
        '<div class="main-title">Generation Response</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 9: Generate final answer using GPT-4o mini.</div>',
        unsafe_allow_html=True
    )

    if "final_context_chunks" not in st.session_state:
        st.warning("No context chunks found. Please complete retrieval or reranking first.")
        return

    if "original_query" not in st.session_state:
        st.warning("No original query found.")
        return

    st.success("Context chunks are ready for generation.")

    st.subheader("Generation Model")
    st.info(f"Model: {GPT_MODEL_NAME}")

    if st.button("Load GPT Client"):
        try:
            client = load_gpt_client()
            st.session_state["gpt_client"] = client
            st.session_state["gpt_generation_loaded"] = True
            st.success("GPT client loaded successfully.")
        except Exception as e:
            st.error(f"Failed to load GPT client: {e}")

    st.markdown("---")

    st.subheader("User Query")
    st.write(st.session_state["original_query"])

    st.subheader("Context Chunks Used")

    for rank, chunk in enumerate(st.session_state["final_context_chunks"], start=1):
        metadata = chunk.get("metadata", {})
        heading_preview = metadata.get("heading", "")[:70]
        st.markdown(f"### Chunk {rank} | ID: {chunk['chunk_id']}")
        st.text_area(
            f"Chunk {chunk['chunk_id']}",
            chunk["text"],
            height=150,
            key=f"gen_chunk_{chunk['chunk_id']}"
        )
        with st.expander("📄 View in Document"):
            show_chunk_source(chunk, key_suffix=f"gen_{rank}")

    if st.session_state.get("gpt_generation_loaded"):
        if st.button("Generate Final Answer"):
            try:
                with st.spinner("Generating answer with GPT-4o mini..."):
                    answer = generate_answer_with_gpt(
                        query=st.session_state["original_query"],
                        context_chunks=st.session_state["final_context_chunks"],
                        client=st.session_state["gpt_client"]
                    )

                st.session_state["generated_answer"] = answer
                st.session_state["generation_done"] = True

                st.success("Answer generated successfully.")

            except Exception as e:
                st.error(f"Generation failed: {e}")

    if st.session_state.get("generation_done"):
        st.markdown("---")
        st.subheader("Final Answer")

        st.text_area(
            "Answer",
            st.session_state["generated_answer"],
            height=300
        )
if st.session_state["page"] == "ingestion":
    show_ingestion_page()

elif st.session_state["page"] == "preprocessing":
    show_preprocessing_page()

elif st.session_state["page"] == "chunking":
    show_chunking_page()
elif st.session_state["page"] == "embedding":
    show_embedding_page()
elif st.session_state["page"] == "image_description":
    show_image_description_page()
elif st.session_state["page"] == "query_expansion":
    show_query_expansion_page()

elif st.session_state["page"] == "retrieval":
    show_retrieval_page()
elif st.session_state["page"] == "reranking":
    show_reranking_page()

elif st.session_state["page"] == "generation":
    show_generation_page()