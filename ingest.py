from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
import os

DOCS_FOLDER = "docs"
INDEX_PATH = "faiss_index"

# --- LOAD ---
all_documents = []
for filename in os.listdir(DOCS_FOLDER):
    if filename.endswith(".pdf"):
        print(f"Loading: {filename}")
        loader = PyPDFLoader(os.path.join(DOCS_FOLDER, filename))
        all_documents.extend(loader.load())
print(f"Loaded {len(all_documents)} pages.")

# --- SPLIT ---
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = splitter.split_documents(all_documents)
print(f"Split into {len(chunks)} chunks.")

# --- EMBED + STORE ---
embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="us-east-1")
print("Embedding all chunks and building vector store...")
vectorstore = FAISS.from_documents(chunks, embeddings)

# --- SAVE TO DISK ---
vectorstore.save_local(INDEX_PATH)
print(f"Vector store saved to '{INDEX_PATH}'. Ingestion complete.")