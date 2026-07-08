from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- Load the saved index ---
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    region_name="us-east-1"
)
vectorstore = FAISS.load_local(
    "faiss_index", embeddings,
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
llm = ChatBedrock(
    model_id="us.anthropic.claude-sonnet-4-6",
    region_name="us-east-1"
)
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

# --- Evaluation set (fact-checked against Wikipedia) ---
EVAL_SET = [
    # --- Core questions (kept from baseline) ---
    {
        "question": "What keyword does Go use to start a goroutine?",
        "expected_keywords": ["go"],
        "source_doc": "Go"
    },
    {
        "question": "What is Rust's approach to memory safety?",
        "expected_keywords": ["borrow checker"],
        "source_doc": "Rust"
    },
    {
        "question": "What paradigms does JavaScript support?",
        "expected_keywords": ["event-driven", "functional", "imperative"],
        "source_doc": "JavaScript"
    },
    {
        "question": "What does Python's design philosophy emphasize?",
        "expected_keywords": ["readability"],
        "source_doc": "Python"
    },
    {
        "question": "How does Go handle concurrency compared to traditional threading?",
        "expected_keywords": ["goroutine", "channel"],
        "source_doc": "Go"
    },
    # --- Hard questions (stress test) ---
    {
        "question": "What are the differences between Python and Java typing systems?",
        "expected_keywords": ["dynamic", "static"],
        "source_doc": "Python + Java"
    },
    {
        "question": "Which language was created by Graydon Hoare?",
        "expected_keywords": ["rust"],
        "source_doc": "Rust"
    },
    {
        "question": "What is the name of Rust's package manager?",
        "expected_keywords": ["cargo"],
        "source_doc": "Rust"
    },
	{
    "question": "What is the most popular cloud provider in 2024?",
    "expected_keywords": ["don't know", "not", "context"],
    "source_doc": "None"
	},
]

# --- Run evaluation ---
print("Running evaluation...\n")
results = []

for item in EVAL_SET:
    answer = rag_chain.invoke(item["question"])
    answer_lower = answer.lower()

    keywords_found = all(
        kw.lower() in answer_lower
        for kw in item["expected_keywords"]
    )

    results.append({
        "question": item["question"],
        "answer": answer,
        "expected_keywords": item["expected_keywords"],
        "passed": keywords_found
    })

    status = "✅ PASS" if keywords_found else "❌ FAIL"
    print(f"{status} | {item['question']}")
    if not keywords_found:
        print(f"       Expected keywords: {item['expected_keywords']}")
        print(f"       Got: {answer[:150]}...")
    print()

# --- Score ---
passed = sum(1 for r in results if r["passed"])
total = len(results)
score = (passed / total) * 100

print(f"{'='*50}")
print(f"BASELINE SCORE: {passed}/{total} ({score:.0f}%)")
print(f"{'='*50}")