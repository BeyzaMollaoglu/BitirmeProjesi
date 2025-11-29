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
except Exception:
    qa_chain = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    if not qa_chain:
        return jsonify({"error": "Sistem hatası"}), 500
    
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "Boş soru"}), 400

    try:
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        source_docs = result.get("source_documents", [])
        
        suggestions = []
        
        for doc in source_docs:
            meta_url = doc.metadata.get("url", "").strip()
            meta_title = doc.metadata.get("title", "").strip()
            
            if meta_url and meta_url.startswith("http"):
                display_title = meta_title if len(meta_title) < 40 else "İlgili Sayfaya Git"
                suggestions.append({"title": display_title, "url": meta_url})
                break
        
        return jsonify({
            "answer": answer,
            "suggestions": suggestions
        })

    except Exception:
        return jsonify({"error": "Hata oluştu"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)