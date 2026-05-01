# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate

app = Flask(__name__)

prompt_template = """You are an expert AI Financial Analyst Assistant.
Use the following pieces of context from market reports to answer the user's question.
Provide insights that would help a quantitative trader make decisions.
If you don't know the answer, just say you don't know. Do NOT hallucinate financial data.

Context: {context}

Question: {question}

Financial Analyst Answer:"""
TRADING_PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

embeddings = None
vector_store = None

def get_vector_store():
    global embeddings, vector_store
    if vector_store is None:
        print("[SYSTEM] Initializing Ollama Embeddings...")
        embeddings = OllamaEmbeddings(model="llama3.2:1b")
        vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        print("[SYSTEM] ChromaDB READY!")
    return vector_store

@app.route("/ingest", methods=["POST"])
def ingest_report():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file_path = f"temp_{file.filename}"
    file.save(file_path)
    loader = TextLoader(file_path) if file.filename.endswith(".txt") else PyPDFLoader(file_path)
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(loader.load())
    vs = get_vector_store()
    vs.add_documents(chunks)
    os.remove(file_path)
    return jsonify({"message": f"Ingested {len(chunks)} chunks."})

@app.route("/ask", methods=["POST"])
def ask_bot():
    data = request.get_json()
    question = data.get("question")
    vs = get_vector_store()
    qa_chain = RetrievalQA.from_chain_type(
        llm=OllamaLLM(model="llama3.2:1b"),
        chain_type="stuff",
        retriever=vs.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": TRADING_PROMPT}
    )
    response = qa_chain.invoke(question)
    return jsonify({"result": response['result']})

if __name__ == "__main__":
    print("[SYSTEM] Starting Flask RAG Server on port 8002...")
    app.run(host="127.0.0.1", port=8002, debug=True, use_reloader=False)