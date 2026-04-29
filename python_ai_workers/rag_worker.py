import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

app = FastAPI()
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

class QueryRequest(BaseModel): question: str

@app.post("/ingest")
async def ingest_report(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f: f.write(await file.read())
    loader = TextLoader(file_path) if file.filename.endswith(".txt") else PyPDFLoader(file_path)
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(loader.load())
    vector_store.add_documents(chunks)
    os.remove(file_path)
    return {"message": f"Ingested {len(chunks)} chunks for Quant Trading."}

@app.post("/ask")
def ask_bot(request: QueryRequest):
    qa_chain = RetrievalQA.from_chain_type(llm=Ollama(model="llama3.2:1b"), retriever=vector_store.as_retriever(search_kwargs={"k": 3}))
    return {"answer": qa_chain.invoke(request.question)['result']}
