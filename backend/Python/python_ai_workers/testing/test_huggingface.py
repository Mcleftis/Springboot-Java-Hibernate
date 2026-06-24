from langchain_huggingface import HuggingFaceEmbeddings

print("\n[ΤΕΣΤ] 1. Ξεκινάει το κατέβασμα/φόρτωση του AI μοντέλου...")
emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
print("[ΤΕΣΤ] 2. ΤΕΛΟΣ! Το μοντέλο φορτώθηκε επιτυχώς. Το laptop πετάει.\n")