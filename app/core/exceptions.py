class DocuMindException(Exception):
    """Base exception for all DocuMind errors."""
    pass


class DocumentNotFoundError(DocuMindException):
    def __init__(self, doc_id: str):
        super().__init__(f"Document '{doc_id}' not found.")


class EmbeddingError(DocuMindException):
    def __init__(self, detail: str):
        super().__init__(f"Embedding failed: {detail}")


class LLMError(DocuMindException):
    def __init__(self, detail: str):
        super().__init__(f"LLM error: {detail}")


class VectorStoreError(DocuMindException):
    def __init__(self, detail: str):
        super().__init__(f"Vector store error: {detail}")