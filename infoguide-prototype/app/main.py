import streamlit as st
from ingestion import save_uploaded_file, extract_text
from preprocessing import preprocess_text
from chunking import (
    heading_based_chunk_text,
    save_chunks
)
from embeddings import (
    MODEL_NAME as BGE_MODEL_NAME,
    load_bge_model,
    load_chunks,
    create_embeddings_one_by_one,
    save_embeddings
)

from query_processing import (
    GPT_MODEL_NAME,
    load_gpt_client,
    expand_query_with_gpt,
    create_query_embedding
)

from retrieval import (
    load_embeddings_and_metadata,
    build_faiss_index,
    retrieve_with_faiss,
    build_bm25_index,
    retrieve_with_bm25
)
from generation import (
    GPT_MODEL_NAME,
    load_gpt_client,
    generate_answer_with_gpt
)
from reranking import load_reranker_model, rerank_results
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
        '<div class="subtitle">Step 1: Upload a document and run ingestion.</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload your document",
        type=["pdf", "txt", "docx"]
    )

    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")

        if st.button("Run Ingestion"):
            try:
                file_path = save_uploaded_file(uploaded_file)
                extracted_text = extract_text(file_path)

                st.session_state["uploaded_file_path"] = str(file_path)
                st.session_state["extracted_text"] = extracted_text
                st.session_state["ingestion_done"] = True

                st.success("Ingestion completed successfully.")

            except Exception as e:
                st.error(f"Ingestion failed: {e}")

    if st.session_state.get("ingestion_done"):
        st.markdown("---")
        st.subheader("Extracted Text Preview")

        st.text_area(
            "Preview",
            st.session_state["extracted_text"],
            height=300
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
        '<div class="subtitle">Step 2: Clean and prepare the extracted text before chunking.</div>',
        unsafe_allow_html=True
    )

    st.success("Ingestion data is ready.")

    st.subheader("Original Extracted Text")

    st.text_area(
        "Original Text",
        st.session_state.get("extracted_text", ""),
        height=300
    )

    if st.button("Run Preprocessing"):
        try:
            original_text = st.session_state.get("extracted_text", "")

            preprocessed_text, logs = preprocess_text(original_text)

            st.session_state["preprocessed_text"] = preprocessed_text
            st.session_state["preprocessing_logs"] = logs
            st.session_state["preprocessing_done"] = True

            for log in logs:
                st.info(log)

            st.success("Preprocessing completed successfully.")

        except Exception as e:
            st.error(f"Preprocessing failed: {e}")

    if st.session_state.get("preprocessing_done"):
        st.subheader("Preprocessed Text")

        st.text_area(
            "Preprocessed Text",
            st.session_state["preprocessed_text"],
            height=300
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
        '<div class="subtitle">Step 3: Create chunks using heading-based chunking.</div>',
        unsafe_allow_html=True
    )

    st.success("Preprocessed text is ready.")

    st.subheader("Selected Chunking Method")
    st.info("Method: Heading-Based Chunking")

    st.markdown(
        """
        This method detects headings such as:

        - 1 Introduction
        - 2.1 Risk Management
        - CHAPTER 3
        - SECTION 4
        - # Markdown Heading

        Then it groups the text under each heading into chunks.
        """
    )

    if st.button("Start Heading-Based Chunking"):
        try:
            preprocessed_text = st.session_state.get("preprocessed_text", "")

            if not preprocessed_text:
                st.warning("No preprocessed text found. Please complete preprocessing first.")
                return

            with st.spinner("Heading-based chunking is running..."):
                chunks, logs = heading_based_chunk_text(preprocessed_text)
                output_path = save_chunks(chunks)

            st.session_state["chunks"] = chunks
            st.session_state["chunking_logs"] = logs
            st.session_state["chunking_done"] = True
            st.session_state["chunks_output_path"] = str(output_path)

            for log in logs:
                st.info(log)

            st.success("Chunking finished successfully.")

        except Exception as e:
            st.error(f"Chunking failed: {e}")

    if st.session_state.get("chunking_done"):
        st.markdown("---")
        st.success("Step 3 completed: Chunking is finished.")

        st.info(f"Chunks saved to: {st.session_state['chunks_output_path']}")

        chunks = st.session_state.get("chunks", [])

        st.subheader("Chunk Preview")

        for chunk in chunks[:5]:
            st.markdown(f"### Chunk {chunk['chunk_id']}")

            if "heading" in chunk:
                st.info(f"Heading: {chunk['heading']}")

            if "sub_chunk_id" in chunk:
                st.caption(f"Sub-chunk: {chunk['sub_chunk_id']}")

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

                vectors = create_embeddings_one_by_one(
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
    if st.session_state.get("embedding_done"):
        st.markdown("---")

        if st.button("Continue to Query Processing"):
            st.session_state["page"] = "query_expansion"
            st.rerun()
def show_query_expansion_page():
    st.markdown(
        '<div class="main-title">Query Expansion</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Step 5: Expand the query with GPT-4o mini and create query embedding.</div>',
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

                st.session_state["gpt_full_output"] = full_output
                st.session_state["expanded_query"] = expanded_query
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

        if st.button("Create Query Embedding"):
            try:
                expanded_query = st.session_state["expanded_query"]

                if "bge_model" not in st.session_state:
                    st.warning("BGE model is not loaded. Please go back to Embedding page.")
                    return

                with st.spinner("Creating query embedding with BGE-M3..."):
                    query_vector = create_query_embedding(
                        expanded_query,
                        st.session_state["bge_model"]
                    )

                st.session_state["query_vector"] = query_vector
                st.session_state["query_embedding_done"] = True

                st.success("Query embedding created successfully.")
                st.info(f"Query vector shape: {query_vector.shape}")

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
        '<div class="subtitle">Step 6: Retrieve relevant chunks using FAISS or BM25.</div>',
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
        ["FAISS", "BM25"]
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

            if retrieval_method == "FAISS":
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
                expanded_query = st.session_state["expanded_query"]

                if retrieval_method == "FAISS":
                    results = retrieve_with_faiss(
                        st.session_state["query_vector"],
                        st.session_state["faiss_index"],
                        metadata,
                        top_k=top_k
                    )

                else:
                    results = retrieve_with_bm25(
                        expanded_query,
                        st.session_state["bm25_index"],
                        metadata,
                        top_k=top_k
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
        '<div class="subtitle">Step 7: Rerank retrieved chunks using BGE reranker.</div>',
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
                        query=expanded_query,
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
        '<div class="subtitle">Step 8: Generate final answer using GPT-4o mini.</div>',
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

    # 🔥 LOAD CLIENT
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
        st.markdown(f"### Chunk {rank} | ID: {chunk['chunk_id']}")
        st.text_area(
            f"Chunk {chunk['chunk_id']}",
            chunk["text"],
            height=150
        )

    # 🔥 GENERATE
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
elif st.session_state["page"] == "query_expansion":
    show_query_expansion_page()

elif st.session_state["page"] == "retrieval":
    show_retrieval_page()
elif st.session_state["page"] == "reranking":
    show_reranking_page()

elif st.session_state["page"] == "generation":
    show_generation_page()