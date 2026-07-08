from langchain_community.document_loaders import PyPDFLoader
import os

# The folder where your PDFs live
docs_folder = "docs"

# We'll collect all the loaded documents here
all_documents = []

# Loop through every file in the docs folder
for filename in os.listdir(docs_folder):
    if filename.endswith(".pdf"):
        filepath = os.path.join(docs_folder, filename)
        print(f"Loading: {filename}")
        loader = PyPDFLoader(filepath)
        pages = loader.load()          # returns a list of Documents, one per page
        all_documents.extend(pages)    # add them to our master list

# Show what we ended up with
print(f"\nTotal documents (pages) loaded: {len(all_documents)}")
print(f"\n--- Preview of the first page ---")
print(all_documents[0].page_content[:300])   # first 300 characters of the first page
print(f"\n--- Metadata of the first page ---")
print(all_documents[0].metadata)

# --- STEP 2: SPLIT into chunks ---
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Create the splitter: ~1000-character chunks, 150 characters of overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)

# Split all our loaded pages into chunks
chunks = text_splitter.split_documents(all_documents)

print(f"\n--- After splitting ---")
print(f"Pages before splitting: {len(all_documents)}")
print(f"Chunks after splitting: {len(chunks)}")
print(f"\n--- Preview of one chunk ---")
print(chunks[10].page_content)
print(f"\n--- That chunk's metadata ---")
print(chunks[10].metadata)

# --- STEP 3: EMBED the chunks ---
from langchain_aws import BedrockEmbeddings

# Set up the Titan embeddings model on Bedrock
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    region_name="us-east-1",
)

# Quick test: embed a single short piece of text to confirm it works
test_vector = embeddings.embed_query("What is the Go programming language?")

print(f"\n--- Embedding test ---")
print(f"The test sentence became a vector of {len(test_vector)} numbers.")
print(f"First 5 numbers: {test_vector[:5]}")

# --- STEP 4: STORE in a FAISS vector store ---
from langchain_community.vectorstores import FAISS

print(f"\n--- Building vector store (embedding all {len(chunks)} chunks)... ---")

# This embeds every chunk and stores them in FAISS, ready to search
vectorstore = FAISS.from_documents(chunks, embeddings)

print("Vector store built successfully.")

# Quick test: search for chunks most relevant to a question
query = "How does Go handle concurrency?"
results = vectorstore.similarity_search(query, k=3)

print(f"\n--- Search test: '{query}' ---")
print(f"Found {len(results)} relevant chunks. Top result:\n")
print(results[0].page_content[:400])
print(f"\n(from: {results[0].metadata['source']}, page {results[0].metadata['page']})")

# --- STEP 5: ANSWER using Claude, built with the pipe (LCEL) ---
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. The answering model
llm = ChatBedrock(
    model_id="us.anthropic.claude-sonnet-4-6",
    region_name="us-east-1",
)

# 2. The retriever (fetches the 3 closest chunks)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. The prompt: we tell Claude to answer ONLY from the retrieved context
prompt = ChatPromptTemplate.from_template(
    """Answer the question using ONLY the context below.
If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}

Answer:"""
)

# 4. A small helper to turn retrieved chunks into one text block
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 5. THE PIPE — assemble the RAG chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 6. Ask a real question
question = "What is Rust's approach to memory safety?"
answer = rag_chain.invoke(question)

print(f"\n=== QUESTION ===\n{question}")
print(f"\n=== ANSWER ===\n{answer}")