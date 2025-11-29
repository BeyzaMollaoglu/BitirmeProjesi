import os
import glob
import re
from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader

load_dotenv(find_dotenv(), override=True)
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("HATA: API Anahtarı yok.")
    exit()

DATA_PATH = "dataset"
VECTOR_DB_PATH = "faiss_index_gsu"
EMBEDDING_MODEL = "text-embedding-3-small"

def load_text_with_metadata(file_path):
    """
    TXT dosyasını okur, ilk satırdaki URL'i ve BAŞLIĞI ayıklar,
    bunu belgenin 'metadata'sına ekler.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    url_match = re.search(r'^URL: (https?://[^\s]+)', content, re.MULTILINE)
    title_match = re.search(r'^BAŞLIK: (.*)', content, re.MULTILINE)

    url = url_match.group(1) if url_match else ""
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    return Document(
        page_content=content,
        metadata={"source": file_path, "url": url, "title": title}
    )

def main():
    documents = []
    
    txt_files = glob.glob(f"{DATA_PATH}/**/texts/*.txt", recursive=True)
    if not txt_files: txt_files = glob.glob(f"{DATA_PATH}/**/*.txt", recursive=True) # Yedek yol

    print(f"📂 {len(txt_files)} Web sayfası (TXT) analiz ediliyor...")
    
    for file_path in tqdm(txt_files, desc="Web Verisi İşleniyor"):
        try:
            doc = load_text_with_metadata(file_path)
            documents.append(doc)
        except Exception as e:
            continue

    other_files = []
    other_files.extend(glob.glob(f"{DATA_PATH}/**/*.pdf", recursive=True))
    other_files.extend(glob.glob(f"{DATA_PATH}/**/*.docx", recursive=True))

    print(f"📂 {len(other_files)} Doküman (PDF/Word) analiz ediliyor...")

    for file_path in tqdm(other_files, desc="Doküman İşleniyor"):
        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".docx"):
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                continue

            docs = loader.load()
            for doc in docs:
                doc.metadata["url"] = "" 
                doc.metadata["title"] = os.path.basename(file_path)
                documents.append(doc)
        except:
            continue

    if not documents:
        print("HATA: Hiçbir veri yüklenemedi.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    print(f"\n🧠 {len(splits)} parça bilgi hafızaya işleniyor (Embedding)...")

    try:
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=api_key)

        batch_size = 100
        vectorstore = FAISS.from_documents(splits[:batch_size], embeddings)
        
        for i in tqdm(range(batch_size, len(splits), batch_size), desc="Vektör Kaydı"):
            vectorstore.add_documents(splits[i : i + batch_size])
            
        vectorstore.save_local(VECTOR_DB_PATH)
        print(f"\n✅ BAŞARILI! Tüm veriler URL kimlikleriyle beraber kaydedildi.")
        
    except Exception as e:
        print(f"\nHATA: {e}")

if __name__ == "__main__":
    main()