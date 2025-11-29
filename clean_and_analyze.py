import os
import glob

DATA_TXT_DIR = "dataset/texts"
MIN_FILE_SIZE = 100  

def analyze_data():
    txt_files = glob.glob(os.path.join(DATA_TXT_DIR, "*.txt"))
    pdf_files = glob.glob("dataset/documents/pdf/*.pdf")
    doc_files = glob.glob("dataset/documents/word/*.docx")
    
    print(f"📊 VERİ ANALİZ RAPORU")
    print("------------------------------------------------")
    print(f"Toplam İndirilen Sayfa (TXT): {len(txt_files)}")
    print(f"Toplam PDF Dokümanı: {len(pdf_files)}")
    print(f"Toplam Word Dokümanı: {len(doc_files)}")
    
    deleted_count = 0
    total_size = 0
    
    for f in txt_files:
        size = os.path.getsize(f)
        if size < MIN_FILE_SIZE:
            try:
                os.remove(f)
                deleted_count += 1
            except:
                pass
        else:
            total_size += size

    print("------------------------------------------------")
    print(f"🗑️  Silinen Boş/Hatalı Dosya: {deleted_count}")
    print(f"✅ Geçerli Metin Dosyası: {len(txt_files) - deleted_count}")
    estimated_tokens = total_size / 4
    print(f"🔠 Tahmini Toplam Kelime/Token: {int(estimated_tokens):,} Token")
    print(f"💰 Tahmini Embedding Maliyeti (text-embedding-3-small): ~${(estimated_tokens/1000000)*0.02:.4f}")
    print("------------------------------------------------")

    if (len(txt_files) - deleted_count) > 500:
        print("SONUÇ: Veri seti fazlasıyla yeterli! Embedding işlemine geçebilirsin.")
    else:
        print("UYARI: Veri sayısı beklenenden az. Crawler ayarlarını kontrol et.")

if __name__ == "__main__":
    analyze_data()