import time
from app.services.embedder import embedder_service
from app.services.vector_store import vector_store_service, RetrievedChunk
from app.services.llm import ollama_service
from app.core.config import get_settings
from app.core.logging import logger
from app.monitoring.metrics import (
    RAG_LATENCY, LLM_LATENCY, CHUNKS_RETRIEVED
)
from typing import AsyncGenerator

settings = get_settings()

RAG_PROMPT_TEMPLATE = """You are a helpful assistant. Answer the question using ONLY the context provided below.
If the context does not contain enough information to answer, say "I don't have enough information to answer that."
Do not make up information.

Context:
{context}

Question: {question}

Answer:"""


class RAGPipeline:
    async def query(self, question: str, top_k: int) -> tuple[str, list[RetrievedChunk]]:
        """
        Full RAG flow:
        1. Embed the question
        2. Retrieve top_k similar chunks from ChromaDB
        3. Build a context-augmented prompt
        4. Generate answer with Ollama
        """
        logger.info(f"RAG query: '{question}' (top_k={top_k})")
        rag_start = time.time()

        # Step 1: embed the question
        query_embedding = embedder_service.embed(question)

        # Step 2: retrieve relevant chunks
        chunks = vector_store_service.query(query_embedding, top_k=top_k)
        CHUNKS_RETRIEVED.observe(len(chunks))

        if not chunks:
            logger.warning("No relevant chunks found — answering without context")
            llm_start = time.time()
            answer = await ollama_service.generate(question)
            LLM_LATENCY.observe(time.time() - llm_start)
            RAG_LATENCY.observe(time.time() - rag_start)
            return answer, []

        # Step 3: build prompt with context
        context = "\n\n---\n\n".join(
            f"[Source: {c.filename}, chunk {c.chunk_index}]\n{c.text}"
            for c in chunks
        )
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

        # Step 4: generate
        llm_start = time.time()
        answer = await ollama_service.generate(prompt)
        LLM_LATENCY.observe(time.time() - llm_start)
        RAG_LATENCY.observe(time.time() - rag_start)

        logger.info(f"RAG answer generated from {len(chunks)} chunks")
        return answer, chunks

    async def query_stream(self, question: str, top_k: int) -> AsyncGenerator[str, None]:
        """Streaming version — same retrieval, but streams the LLM response."""
        query_embedding = embedder_service.embed(question)
        chunks = vector_store_service.query(query_embedding, top_k=top_k)
        CHUNKS_RETRIEVED.observe(len(chunks))

        if chunks:
            context = "\n\n---\n\n".join(
                f"[Source: {c.filename}, chunk {c.chunk_index}]\n{c.text}"
                for c in chunks
            )
            prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
        else:
            prompt = question

        async for token in ollama_service.generate_stream(prompt):
            yield token


rag_pipeline = RAGPipeline()