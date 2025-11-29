import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv(), override=True)
VECTOR_DB_PATH = "faiss_index_gsu"

print("🧠 Beyin yükleniyor...")

try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    
    print("✅ Beyin hazır! Sorunu sorabilirsin (Çıkmak için 'q' bas).")
    
    while True:
        query = input("\nSoru: ")
        if query.lower() == 'q': break
        
        # Cevapla
        result = qa_chain.invoke({"query": query})
        
        print(f"\n🤖 Cevap: {result['result']}")
        print("\n📚 Kaynaklar:")
        for doc in result["source_documents"]:
            print(f"- {os.path.basename(doc.metadata.get('source', 'Bilinmiyor'))}")

except Exception as e:
    print(f"❌ HATA: {e}")