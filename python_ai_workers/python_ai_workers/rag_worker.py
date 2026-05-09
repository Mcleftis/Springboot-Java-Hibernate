import os
from flask import Flask, request, jsonify
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

app = Flask(__name__)

system_prompt = (
    "You are an expert AI Financial Analyst Assistant. "
    "Use the following pieces of retrieved context to answer the user's question. "
    "If you don't know the answer, just say you don't know. "
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

embeddings = None
vector_store = None

def get_vector_store():
    global embeddings, vector_store
    if vector_store is None:
        embeddings = OllamaEmbeddings(model="llama3.2:1b")
        vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
    return vector_store

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/ingest_local", methods=["POST"])
def ingest_local_files():
    files_to_load = ["lstm_output.txt", "quant_output.txt"]
    all_chunks = []

    for file_path in files_to_load:
        if os.path.exists(file_path):
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                chunks = splitter.split_documents(docs)
                all_chunks.extend(chunks)
            except Exception as e:
                return jsonify({"error": f"Failed to load {file_path}: {str(e)}"}), 500

    if not all_chunks:
        return jsonify({"error": "No output files found to ingest."}), 400

    try:
        vs = get_vector_store()
        vs.add_documents(all_chunks)
    except Exception as e:
        return jsonify({"error": f"Failed to add documents to vector store: {str(e)}"}), 500

    return jsonify({
        "message": f"Ingested {len(all_chunks)} chunks from local worker outputs."
    })

@app.route("/ask", methods=["POST"])
def ask_bot():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Missing 'question' field in request body."}), 400

    question = data.get("question")

    try:
        vs = get_vector_store()
        retriever = vs.as_retriever(search_kwargs={"k": 3})
        llm = OllamaLLM(model="llama3.2:1b")

        chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        result = chain.invoke(question)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Failed to process question: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8002, debug=True, use_reloader=False)
