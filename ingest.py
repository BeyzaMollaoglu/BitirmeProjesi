import os
import glob
import time
import logging
from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

logging.getLogger("pypdf").setLevel(logging.ERROR)

load_dotenv(find_dotenv(), override=True)
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("HATA: .env dosyasında API anahtarı bulunamadı.")
    exit()

DATA_PATH = "dataset"
VECTOR_DB_PATH = "faiss_index_gsu"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

def main():
    documents = []
    
    files = []
    for ext in ["*.txt", "*.pdf", "*.docx"]:
        files.extend(glob.glob(f"{DATA_PATH}/**/{ext}", recursive=True))

    if not files:
        print("HATA: Dosya bulunamadı.")
        return

    print(f"{len(files)} dosya işleniyor...")

    for file_path in tqdm(files, desc="Dosya Okuma"):
        try:
            if file_path.endswith(".txt"):
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".docx"):
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                continue
            documents.extend(loader.load())
        except:
            continue 

    if not documents:
        print("HATA: İçerik okunamadı.")
        return

    print("Metinler parçalanıyor...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    
    total_chunks = len(splits)
    print(f"\nToplam {total_chunks} vektör parçası oluşturuldu.")
    print(f"Embedding işlemi başlıyor (Batch Size: {BATCH_SIZE})...")

    try:
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=api_key)
        
        vectorstore = FAISS.from_documents(splits[:BATCH_SIZE], embeddings)
        
        for i in tqdm(range(BATCH_SIZE, total_chunks, BATCH_SIZE), desc="Vektör Kaydı"):
            batch = splits[i : i + BATCH_SIZE]
            vectorstore.add_documents(batch)
            time.sleep(0.1) 

        vectorstore.save_local(VECTOR_DB_PATH)
        print(f"\n✅ BAŞARILI! Tüm veriler '{VECTOR_DB_PATH}' klasörüne kaydedildi.")
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")

if __name__ == "__main__":
    main()