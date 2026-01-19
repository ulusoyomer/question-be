# Backend API

Soru uygulamasının sunucu tarafı servisidir. **Python**, **FastAPI** ve **SQLAlchemy** kullanılarak geliştirilmiştir. PDF işleme, AI üretimi (OpenRouter üzerinden), oturum yönetimi (SQLite) ve görsel depolama işlemlerini yürütür.

## 🛠 Teknoloji Yığını

*   **Framework**: FastAPI
*   **Veritabanı**: SQLite (yerel dosya: `voltran.db`)
*   **ORM**: SQLAlchemy
*   **AI Entegrasyonu**: OpenRouter API (Anthropic Claude 3.5 Sonnet)
*   **Ayarlar**: Pydantic Settings
*   **Sunucu**: Uvicorn

## 🚀 Kurulum

### Gereksinimler
*   Python 3.10 veya üzeri
*   pip

### Adımlar

1.  **Sanal Ortam Oluşturma (Virtual Environment)**
    ```bash
    python -m venv venv
    
    # Mac/Linux
    source venv/bin/activate
    
    # Windows
    venv\Scripts\activate
    ```

2.  **Bağımlılıkları Yükleme**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ortam Değişkenleri (.env)**
    Bu dizinde `.env` dosyası oluşturun ve aşağıdaki değişkenleri ekleyin:
    ```env
    OPENROUTER_API_KEY=sk-or-v1-...  # OpenRouter API Anahtarınız
    MODEL_NAME=anthropic/claude-3.5-sonnet
    BACKEND_URL=http://localhost:80   # Emülatör/Cihaz tarafından erişilebilir URL
    ```

4.  **Sunucuyu Başlatma**
    ```bash
    # 80 Portunda çalıştır (Emülatörden erişim kolaylığı için)
    # Not: Mac/Linux'ta 80 portu sudo gerektirebilir
    sudo python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 80
    
    # Veya varsayılan 8000 portunda çalıştır
    # python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

    API dokümantasyonuna şuradan erişebilirsiniz:
    *   Swagger UI: `http://localhost:80/docs`
    *   ReDoc: `http://localhost:80/redoc`

## 📂 Proje Yapısı

```
backend/
├── app/
│   ├── database/    # Modeller, CRUD işlemleri, Veritabanı bağlantısı
│   ├── routers/     # API Uç Noktaları (üretim, geçmiş, benzerlik, iyileştirme)
│   ├── services/    # İş Mantığı (AIService)
│   ├── utils/       # Yardımcı fonksiyonlar, Promptlar, Şemalar
│   ├── config.py    # Yapılandırma ayarları
│   └── main.py      # Başlangıç noktası
├── uploads/         # Yüklenen soru görsellerinin saklandığı klasör
├── requirements.txt # Python bağımlılıkları
└── voltran.db       # SQLite veritabanı dosyası (otomatik oluşturulur)
```

## 🔑 Temel Özellikler

*   **PDF Üretimi**: PDF'lerden metin çıkarır ve yapılandırılmış sorular üretir.
*   **Style Clone**: Gelen görselleri (Base64) işler, OCR (Claude Vision) ile metni okur, diske kaydeder ve benzer sorular üretir.
*   **Çoklu Dil**: İstendiğinde yapay zekayı Türkçe çıktı vermeye zorlayan özel prompt yapıları içerir.
*   **Statik Sunum**: `/uploads` uç noktası üzerinden görselleri dışarıya açar.

---

## 🤖 AI Kullanım Raporu & Mühendislik Süreci

Bu backend projesi, "AI-First" ancak "İnsan Mimarisinde" bir yaklaşımla geliştirilmiştir. Geliştirme sürecini hızlandırmak için Cursor ("Agent" modu) gibi araçlar kullanılmış, ancak katı mühendislik standartlarından ödün verilmemiştir. Sadece kod yazdırmak ("vibe coding") yerine, AI'ı spesifik problemlere çözüm üreten bir mühendislik asistanı olarak kullandık.

### 1. JSON Şema Zorlama (JSON Schema Enforcement)
**Problem**: LLM'ler genellikle serbest metin üretmeye meyillidir. Regex ile çıktı ayıklamak kırılgandır ve bakım maliyeti yüksektir.
**Çözüm**: "Schema-First" yaklaşımı benimsedik.
*   `backend/app/utils/schemas.py` dosyasında katı Pydantic modelleri tanımladık.
*   System Prompt içerisine bu şemayı dinamik olarak enjekte ettik ve şu talimatı verdik: *"You MUST respond with valid JSON that matches this exact schema..."*
*   **Güvenlik Ağı**: Eğer AI bozuk JSON üretirse, bir `try-catch` bloğu hatayı yakalar ve hatayı AI'ya geri besleyerek (re-prompting) düzeltmesini ister. Bu sayede %99.9 oranında valid çıktı elde ettik.

### 2. Çok Adımlı Mantık Zinciri (Tool Chaining)
**Strateji**: "Style Clone" özelliği tek bir LLM çağrısı değildir; orkestre edilmiş bir iş akışıdır.
*   **Adım 1 (Vision)**: Claude 3.5 Sonnet önce görseli analiz eder ve metni/bağlamı çıkarır (OCR).
*   **Adım 2 (Generation)**: Çıkarılan metin, ayrı bir "Soru Üretim" promptuna beslenir.
*   **Neden?**: İki işi tek adımda yapmaya çalışmak (görseli analiz et ve soru üret), halüsinasyon oranını artırıyordu. İşlemi bölmek (Seperation of Concerns), doğruluğu ciddi oranda artırdı.

### 3. AI Destekli Hata Ayıklama (AI Debugging)
**Yaklaşım**: Hata aldığımızda rastgele kod değişikliği yapmak yerine, Terminal çıktılarını ve Stack Trace'i bir veri olarak AI Agent'a besledik.
*   **Örnek (Database Locking)**: Eş zamanlı isteklerde SQLite "database is locked" hatası verdiğinde, Agent bu hatayı analiz etti ve sorunun FastAPI'nin thread yapısı ile SQLite'ın varsayılan bağlantı ayarları arasındaki uyumsuzluk olduğunu tespit etti.
*   **Fix**: Agent, SQLAlchemy bağlantı ayarlarına `check_same_thread=False` argümanını ekleyerek sorunu nokta atışı çözdü.

### 4. Zorluklar & Manuel Müdahaleler (AI'ın Yetersiz Kaldığı Yerler)
AI araçları güçlüdür ancak kusursuz değildir. İşte manuel mühendislik gerektiren bazı durumlar:

*   **Problem: Dil Kararlılığı (Language Stability)**: Girdi Türkçe olsa bile AI, "Benzer Sorular" üretirken İngilizceye dönme eğilimindeydi.
    *   *Manuel Müdahale*: Dinamik prompt oluşturma yerine, `ai_service.py` içinde **sert kodlanmış (hard-coded)** talimatlar ("MUTLAKA TÜRKÇE", "MUST BE TURKISH") kullanarak AI'ın varsayılan davranışını ezdik.

*   **Problem: Görsel Yönetimi**: AI, görselleri Base64 string olarak veritabanına kaydetmeyi önerdi.
    *   *Manuel Müdahale*: Bu yöntemin veritabanını şişireceğini öngörerek, Backend mimarisini değiştirdik. Görselleri diskte (`/uploads`) saklayıp veritabanında sadece URL tutan daha performanslı bir yapı kurduk.
