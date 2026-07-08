import gradio as gr
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

INDEX_PATH = "faiss_index"

# --- Load the saved store and build the RAG chain (once, at startup) ---
embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="us-east-1")
vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
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

# --- The function Gradio calls when you send a message ---
def answer_question(message, history):
    return rag_chain.invoke(message)

# --- Build and launch the chat interface ---
demo = gr.ChatInterface(
    fn=answer_question,
    title="Ask My Docs",
    description="Ask questions about the programming language documents.",
)

if __name__ == "__main__":
    demo.launch()