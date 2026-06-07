# InfoGuide — RAG Pipeline

InfoGuide, kurumsal dokümanlar üzerine soru-cevap yapabilen bir **Retrieval-Augmented Generation (RAG)** sistemidir. PDF, DOCX ve TXT formatındaki dokümanları işleyerek kullanıcı sorgularına kaynak göstererek cevap üretir.

---

## Genel Mimari

```
Doküman Upload
      ↓
  Ingestion          ← metin, tablo ve görselleri çıkar
      ↓
 Preprocessing       ← metni temizle ve normalize et
      ↓
   Chunking          ← heading'e göre parçala, tablo izolasyonu, breadcrumb
      ↓
  Embedding          ← BGE-M3 ile vektöre çevir
      ↓
Image Description    ← GPT-4o Vision ile görsel chunk'ları oluştur
      ↓
Query Expansion      ← GPT-4o-mini ile sorguyu genişlet + sub-query'lere böl
      ↓
  Retrieval          ← Hybrid FAISS + BM25, Multi-Query RRF
      ↓
  Reranking          ← BGE-reranker-v2-m3 CrossEncoder
      ↓
  Generation         ← GPT-4o-mini ile cevap üret
      ↓
Document Viewer      ← kaynak dokümana navigasyon + highlight
```

---

## Backend Bileşenleri

### 1. Ingestion (`ingestion.py`)

Yüklenen dokümanlardan metin, tablo ve görselleri çıkarır.

**PDF:**
- `pdfplumber` ile sayfa bazlı metin extraction
- Tablo bounding box'ları tespit edilip metin extraction'dan dışlanır — tablo ve metin birbirine karışmaz
- Tablolar `pdfplumber` ile ayrıca çekilip markdown formatına dönüştürülür
- `fitz` (PyMuPDF) ile gömülü görseller extract edilir
- Selectable text yoksa `pdf2image` + `pytesseract` ile OCR fallback

**DOCX:**
- `python-docx` ile paragraf, tablo, header/footer extraction
- Görseller inline pozisyonlarıyla birlikte extract edilir

**TXT:** Direkt okuma.

---

### 2. Preprocessing (`preprocessing.py`)

Ham metni temizler: gereksiz boşluklar, özel karakterler, çok satırlı boşluklar normalize edilir.

---

### 3. Chunking (`chunking.py`)

Metni anlamlı parçalara böler.

**Heading tespiti** — şu pattern'lerden biri eşleşirse heading sayılır:
- `1.`, `1.2`, `1.2.3` formatındaki numaralı başlıklar
- `Chapter N`, `Section N`, `CHAPTER N`
- Markdown `#`, `##`, `###`
- Tamamı büyük harf satırlar (harf sayısı > rakam sayısı)

**Recursive splitting:**
- Önce paragraf bazlı bölme
- Paragraf `MAX_CHARS` (1800) aşarsa cümle bazlı bölme
- `OVERLAP_CHARS` (250) ile chunk'lar arası bağlam korunur

**Tablo izolasyonu:**
- Tablolar asla bölünmez, her zaman tek chunk
- `chunk_type: "table_chunk"` olarak işaretlenir

**Parent Heading Breadcrumb:**
- Her başlık için hiyerarşi seviyesi belirlenir (`get_heading_level`)
- `heading_stack` ile parent başlıklar takip edilir
- Sub-section chunk'ların embed metnine tüm parent zinciri eklenir:
  ```
  Section: 1. Risk Yönetimi > 1.2 Limitler > 1.2.3 Günlük Limit
  ```

---

### 4. Embedding (`embeddings.py`)

`BAAI/bge-m3` modeliyle vektörler oluşturulur.

- Chunk'lar için `embed_documents(batch)` — batch size 32
- Sorgular için `embed_query` — asimetrik embedding için doğru API
- Vektörler `np.float32` olarak `data/indexes/embeddings.npy`'e kaydedilir
- Metadata `data/indexes/embeddings_metadata.json`'a kaydedilir

---

### 5. Image Description (`image_description.py`)

Extract edilen görsellerden chunk oluşturur.

- `ThreadPoolExecutor` ile paralel GPT-4o Vision çağrısı (max 5 worker)
- Sıra korunur: indexed `results[i]` array ile
- Yapılandırılmış prompt: IMAGE TYPE, MAIN CONTENT, ALL VISIBLE TEXT, DATA & NUMBERS, STRUCTURE, ENTITIES
- Her görsel için `chunk_type: "image_description"` chunk oluşturulur
- Mevcut chunk'lara append edilerek embedding'e eklenir

---

### 6. Query Processing (`query_processing.py`)

Kullanıcı sorgusunu retrieval için hazırlar.

**Query Expansion:**
- GPT-4o-mini ile sorgudan intent, keywords ve expanded query çıkarılır
- Expanded query embedding için kullanılır

**Query Decomposition:**
- Sorgu birden fazla bağımsız kavram içeriyorsa 2-4 atomik sub-query'e bölünür
- Tek kavramlı sorgu decompose edilmeden bırakılır (temperature: 0.1)
- Her sub-query için ayrı embedding oluşturulur

---

### 7. Retrieval (`retrieval.py`)

İki retriever'ın kombinasyonuyla en alakalı chunk'lar bulunur.

**FAISS (Dense Retrieval):**
- `IndexFlatIP` — inner product = cosine similarity (vektörler normalize)
- Expanded query embedding ile arama

**BM25 (Sparse Retrieval):**
- `BM25Okapi` — TF-IDF tabanlı keyword eşleşmesi
- Noktalama temizlenmiş tokenizer ile

**Hybrid + Multi-Query RRF:**
- Her sub-query için ayrı hybrid retrieval çalışır
- Tüm sonuçlar **Reciprocal Rank Fusion** ile birleştirilir
- Birden fazla sub-query'de geçen chunk'lar daha yüksek skor alır
- `candidate_k = max(top_k × 6, 40)` ile geniş aday havuzu

---

### 8. Reranking (`reranking.py`)

Retrieved chunk'ları orijinal sorguya göre yeniden sıralar.

- `BAAI/bge-reranker-v2-m3` CrossEncoder modeli
- `max_length=512` ile explicit truncation
- Query-chunk çifti birlikte değerlendirilir — embedding'den daha hassas

---

### 9. Generation (`generation.py`)

Final cevabı üretir.

- Model: `gpt-4o-mini`
- Strict RAG system prompt (6 kural):
  1. Sadece verilen context'i kullan
  2. Cevap yoksa: *"The provided documents do not contain..."*
  3. Kullanılan Chunk ID'lerini kaynak olarak göster
  4. Birden fazla chunk'ı sentezle
  5. Image description chunk'larını normal içerik gibi işle
  6. Net, doğru ve eksiksiz ol
- `max_tokens` sınırı yok — modelin kendi sınırına bırakıldı
- Temperature: 0.2

---

### 10. Document Viewer (`main.py`)

Cevap üretildikten sonra her chunk için kaynak dokümana navigasyon sağlar.

**PDF:**
- `fitz` ile orijinal PDF'in geçici bir kopyası oluşturulur
- Chunk heading metni + içerik satırları (>15 karakter) PDF sayfasında aranır
- Bulunan tüm eşleşmeler sarı highlight annotation ile işaretlenir
- Chunk birden fazla sayfaya yayılıyorsa tüm sayfalarda arama yapılır
- HTML redirect (`file:///tmp.pdf#page=N`) ile tarayıcıda doğrudan o sayfada açılır
- Background thread ile çalışır, 15 saniye sonra geçici dosyalar silinir

**DOCX / TXT:**
- `os.startfile()` ile varsayılan uygulama açılır

---

## Veri Akışı

```
data/
├── raw/              ← upload edilen orijinal dosyalar
├── images/           ← extract edilen görseller
├── processed/        ← preprocessed metin
├── chunks/           ← chunks.json
└── indexes/
    ├── embeddings.npy
    └── embeddings_metadata.json
```

---

## Kullanılan Modeller

| Görev | Model |
|-------|-------|
| Embedding | `BAAI/bge-m3` |
| Reranking | `BAAI/bge-reranker-v2-m3` |
| Query Expansion & Generation | `gpt-4o-mini` |
| Image Description | `gpt-4o` |

---

## Teknoloji Stack

| Katman | Kütüphane |
|--------|-----------|
| UI | Streamlit |
| PDF extraction | pdfplumber, pypdf, fitz (PyMuPDF) |
| OCR | pdf2image, pytesseract |
| DOCX extraction | python-docx |
| Embedding | LangChain HuggingFaceEmbeddings |
| Vector search | faiss-cpu |
| Keyword search | rank-bm25 |
| Reranking | sentence-transformers (CrossEncoder) |
| LLM | OpenAI API |
