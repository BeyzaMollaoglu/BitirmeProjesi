import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import os
import re

START_URLS = [
    "https://gsu.edu.tr/tr/",
    "https://muhendislik.gsu.edu.tr/tr/",
    "https://fbe.gsu.edu.tr/tr/",
    "https://sbe.gsu.edu.tr/tr/",
    "https://hukuk.gsu.edu.tr/tr/",
    "https://iletisim.gsu.edu.tr/tr/",
    "https://iibf.gsu.edu.tr/tr/",
    "https://kutuphane.gsu.edu.tr/tr/"
]

ALLOWED_DOMAINS = ["gsu.edu.tr"]
MAX_URLS_TO_CRAWL = 5000

DATA_TXT_DIR = "dataset/texts"
DATA_DOCS_DIR = "dataset/documents"

TARGET_EXTENSIONS = {
    '.pdf': 'pdf',
    '.doc': 'word', '.docx': 'word',
    '.ppt': 'powerpoint', '.pptx': 'powerpoint',
    '.xls': 'excel', '.xlsx': 'excel'
}

IGNORED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.zip', '.rar', 
    '.css', '.js', '.json', '.xml'
]

os.makedirs(DATA_TXT_DIR, exist_ok=True)
for subfolder in set(TARGET_EXTENSIONS.values()):
    os.makedirs(os.path.join(DATA_DOCS_DIR, subfolder), exist_ok=True)

visited_urls = set()
urls_queue = list(START_URLS)

def normalize_url(url):
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

def is_valid_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path.lower()
    
    is_allowed = any(domain.endswith(d) for d in ALLOWED_DOMAINS)
    is_ignored = any(path.endswith(ext) for ext in IGNORED_EXTENSIONS)
    
    return is_allowed and not is_ignored

def save_document(url, response):
    try:
        parsed = urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        
        if ext in TARGET_EXTENSIONS:
            folder_name = TARGET_EXTENSIONS[ext]
            filename = os.path.basename(path)
            if not filename: filename = f"doc_{int(time.time())}{ext}"
            
            save_path = os.path.join(DATA_DOCS_DIR, folder_name, filename)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"   [DOSYA] İndirildi ({folder_name}): {filename}")
            return True
    except Exception as e:
        print(f"   [HATA] Dosya kaydedilemedi: {e}")
    return False

def save_page_text(url, soup):
    try:
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        title_tag = soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else "Basliksiz_Sayfa"

        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        safe_filename = re.sub(r'[^a-zA-Z0-9]', '_', url)
        if len(safe_filename) > 100: safe_filename = safe_filename[:100]
        filepath = os.path.join(DATA_TXT_DIR, f"{safe_filename}.txt")

        if len(clean_text) < 200:
            return False

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n")
            f.write(f"TITLE: {title}\n")
            f.write("="*50 + "\n")
            f.write(clean_text)
        
        return True
    except Exception as e:
        print(f"   [HATA] Metin kaydedilemedi: {e}")
        return False

print(f"🚀 Tarama Başlıyor... Hedef: {ALLOWED_DOMAINS}")
print(f"📂 Veriler 'dataset' klasörüne kaydedilecek.")

processed_count = 0
session = requests.Session()
session.headers.update({'User-Agent': 'GSU_Student_Project_Bot/1.0'})

while urls_queue and processed_count < MAX_URLS_TO_CRAWL:
    current_url = urls_queue.pop(0)
    current_url = normalize_url(current_url)

    if current_url in visited_urls:
        continue

    print(f"[{processed_count + 1}/{MAX_URLS_TO_CRAWL}] Ziyaret ediliyor: {current_url}")
    
    try:
        response = session.get(current_url, timeout=10)
        content_type = response.headers.get('Content-Type', '').lower()
        
        if any(ext in current_url.lower() for ext in TARGET_EXTENSIONS) or \
           'application/pdf' in content_type or \
           'application/msword' in content_type:
            
            if save_document(current_url, response):
                visited_urls.add(current_url)
                processed_count += 1
            continue

        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if save_page_text(current_url, soup):
                processed_count += 1
            
            visited_urls.add(current_url)

            for link in soup.find_all('a', href=True):
                raw_href = link['href']
                full_url = urljoin(current_url, raw_href)
                normalized_next_url = normalize_url(full_url)

                if is_valid_url(normalized_next_url) and normalized_next_url not in visited_urls:
                    urls_queue.append(normalized_next_url)

        time.sleep(0.3)

    except Exception as e:
        print(f"   [HATA] Bağlantı sorunu: {e}")

print("\n🏁 Tarama Tamamlandı!")
print(f"Toplam {processed_count} adet içerik işlendi.")