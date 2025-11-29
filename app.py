from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv(), override=True)

app = Flask(__name__)
CORS(app)

VECTOR_DB_PATH = "faiss_index_gsu"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

try:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
except Exception as e:
    print(f"HATA: Veritabanı yüklenemedi: {e}")
    qa_chain = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    if not qa_chain:
        return jsonify({"error": "Veritabanı yüklü değil."}), 500
    
    data = request.json
    user_question = data.get('question')
    
    if not user_question:
        return jsonify({"error": "Soru boş olamaz."}), 400

    try:
        result = qa_chain.invoke({"query": user_question})
        answer = result["result"]
        
        source_documents = result.get("source_documents", [])
        sources = []
        for doc in source_documents:
            source_name = os.path.basename(doc.metadata.get("source", ""))
            if source_name and source_name not in sources:
                sources.append(source_name)
        
        return jsonify({
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": "Bir hata oluştu."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)