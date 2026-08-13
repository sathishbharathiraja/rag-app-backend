import os
import tempfile
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from langchain_community.document_loaders import TextLoader, Docx2txtLoader
import pymupdf4llm
from langchain_core.documents import Document as LangchainDocument
from app.models.models import Document, DocumentChunk
# Initialize HuggingFace embeddings for local, free document ingestion
from langchain_huggingface import HuggingFaceEmbeddings
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

async def process_and_store_document(
    db: AsyncSession, 
    file_bytes: bytes, 
    filename: str, 
    user_id: int
) -> int:
    """Processes an uploaded file, extracts text, chunks it, embeds it, and stores in PostgreSQL."""
    
    # 1. Create document record
    new_doc = Document(filename=filename, user_id=user_id)
    db.add(new_doc)
    await db.flush()  # To get the doc.id
    
    # 2. Extract text from file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    try:
        if filename.endswith(".pdf"):
            md_text = pymupdf4llm.to_markdown(temp_file_path)
            docs = [LangchainDocument(page_content=md_text)]
        elif filename.endswith(".txt"):
            loader = TextLoader(temp_file_path, autodetect_encoding=True)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(temp_file_path)
        else:
            raise ValueError("Unsupported file format")
            
        if not filename.endswith(".pdf"):
            docs = loader.load()
    finally:
        os.remove(temp_file_path)

    # 3. Split into chunks using Markdown splitters
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    # 4. Generate embeddings and store
    for doc in docs:
        clean_text = doc.page_content.replace("\x00", "")
        # First split by markdown headers
        md_docs = markdown_splitter.split_text(clean_text)
        
        # If markdown splitter produced nothing (e.g. no headers), fallback to raw text
        if not md_docs:
            md_docs = [LangchainDocument(page_content=clean_text)]

        # Then split long sections by character count
        final_docs = text_splitter.split_documents(md_docs)
        
        chunk_texts = []
        for final_doc in final_docs:
            # Include header metadata in the chunk text for the LLM to read
            metadata_str = " ".join([f"{k}: {v}" for k, v in final_doc.metadata.items()])
            chunk_texts.append(f"[{metadata_str}]\n{final_doc.page_content}" if metadata_str else final_doc.page_content)
            
        if chunk_texts:
            import asyncio
            batch_size = 20
            embeddings = []
            
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i + batch_size]
                max_retries = 5
                
                for attempt in range(max_retries):
                    try:
                        batch_embeddings = await embeddings_model.aembed_documents(batch)
                        
                        for chunk_text, embedding in zip(batch, batch_embeddings):
                            chunk = DocumentChunk(
                                doc_id=new_doc.id,
                                text=chunk_text,
                                embedding=embedding
                            )
                            db.add(chunk)
                            
                        # If successful, break retry loop and move to next batch
                        break
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg and "RESOURCE_EXHAUSTED" in error_msg:
                            if attempt < max_retries - 1:
                                # Extract wait time if possible, or fallback to 10s backoff
                                wait_time = 10 * (attempt + 1)
                                if "Please retry in" in error_msg:
                                    try:
                                        import re
                                        match = re.search(r'Please retry in ([\d\.]+)s', error_msg)
                                        if match:
                                            wait_time = float(match.group(1)) + 1.0 # Add 1s buffer
                                    except:
                                        pass
                                
                                await asyncio.sleep(wait_time)
                            else:
                                raise Exception(f"Failed to embed document due to rate limit after {max_retries} retries.") from e
                        else:
                            raise e
            
    await db.commit()
    return new_doc.id

async def similarity_search(db: AsyncSession, query: str, user_id: int, top_k: int = 4) -> List[str]:
    """Finds the most relevant chunks in the database for a given query, scoped to a specific user."""
    query_embedding = await embeddings_model.aembed_query(query)
    
    # Using pgvector's <=> operator for cosine distance, scoped to user and thresholded
    stmt = (
        select(DocumentChunk)
        .join(Document)
        .where(
            Document.user_id == user_id,
            DocumentChunk.embedding.cosine_distance(query_embedding) < 1.2
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    chunks = sorted(chunks, key=lambda c: c.id)
    return [chunk.text for chunk in chunks]
