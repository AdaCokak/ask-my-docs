from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

INDEX_PATH = "faiss_index"

# --- LOAD the saved vector store (fast — no re-embedding) ---
embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="us-east-1")
vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

# --- Set up Claude + the RAG chain ---
llm = ChatBedrock(model_id="us.anthropic.claude-sonnet-4-6", region_name="us-east-1")

prompt = ChatPromptTemplate.from_template(
    """Answer the question using ONLY the context below.
If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}

Answer:"""
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- Ask questions in a loop ---
print("Ask questions about your documents (type 'quit' to exit).\n")
while True:
    question = input("Question: ")
    if question.lower() in ("quit", "exit"):
        break
    answer = rag_chain.invoke(question)
    print(f"\nAnswer: {answer}\n")