import os
import sys
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

print("--------------------------------------------------")
print("1. ADIM: ÇALIŞMA ORTAMI KONTROLÜ")
print("--------------------------------------------------")

current_dir = os.getcwd()
print(f"Python'un çalıştığı klasör: {current_dir}")

env_file = find_dotenv()

if env_file:
    print(f"✅ .env dosyası bulundu! Konumu: {env_file}")
else:
    print("❌ HATA: .env dosyası bulunamadı!")
    print("   Lütfen .env dosyasının yukarıdaki klasörde olduğundan emin ol.")
    print("   Dosya adının başında nokta olduğundan (.env) emin ol.")
    sys.exit()

print("\n--------------------------------------------------")
print("2. ADIM: API ANAHTARI KONTROLÜ")
print("--------------------------------------------------")
load_dotenv(env_file, override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ HATA: Dosya var ama içinde 'OPENAI_API_KEY' bulunamadı.")
    print("   Dosyanın içinde şu formatta yazdığından emin ol:")
    print("   OPENAI_API_KEY=sk-proj-...")
    sys.exit()

print(f"Anahtar Uzunluğu: {len(api_key)} karakter")
print(f"Anahtar Başlangıcı: {api_key[:7]}...") 

if not api_key.startswith("sk-"):
    print("⚠️ UYARI: Anahtarın 'sk-' ile başlamıyor. Yanlış kopyalamış olabilirsin.")
elif " " in api_key:
    print("❌ HATA: Anahtarın içinde BOŞLUK karakteri tespit edildi!")
    print("   Lütfen .env dosyasındaki eşittir işaretinden sonraki boşlukları sil.")
    sys.exit()
else:
    print("✅ Anahtar formatı düzgün görünüyor.")

print("\n--------------------------------------------------")
print("3. ADIM: BAĞLANTI TESTİ")
print("--------------------------------------------------")

try:
    print("OpenAI sunucularına istek gönderiliyor (gpt-5-nano)...")
    
    llm = ChatOpenAI(
        api_key=api_key, 
        model="gpt-5-nano",
        temperature=0.7,
        max_retries=1 
    )

    cevap = llm.invoke("Merhaba, sadece 'Bağlantı Başarılı' yaz.")
    
    print("\n🎉 SONUÇ: BAŞARILI!")
    print(f"Model Cevabı: {cevap.content}")

except Exception as e:
    print("\n❌ SONUÇ: BAĞLANTI BAŞARISIZ")
    print("Hata Detayı:")
    print(e)
    
    error_str = str(e)
    if "401" in error_str:
        print("\n👉 İPUCU: 401 Hatası %100 'Anahtar Yanlış' demektir.")
        print("   1. OpenAI sitesinden yeni bir key oluştur.")
        print("   2. .env dosyasına yapıştırırken başında/sonunda boşluk kalmadığına emin ol.")
    elif "429" in error_str:
        print("\n👉 İPUCU: 429 Hatası 'Kredi Bitti' veya 'Çok Fazla İstek' demektir.")
        print("   Hesabındaki kredileri (Billing kısmını) kontrol etmelisin.")