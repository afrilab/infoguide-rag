# InfoGuide RAG Pipeline — Yapılan Değişiklikler

## İçindekiler
1. [embeddings.py](#1-embeddingspy)
2. [retrieval.py](#2-retrievalpy)
3. [reranking.py](#3-rerankingpy)
4. [image_description.py](#4-image_descriptionpy)
5. [query_processing.py](#5-query_processingpy)
6. [generation.py](#6-generationpy)
7. [chunking.py](#7-chunkingpy)
8. [main.py](#8-mainpy)

---

## 1. embeddings.py

### Sorun: `embed_query` chunk'lara uygulanıyordu
BGE-M3 modelinin doküman chunk'ları için `embed_documents`, sorgular için `embed_query` kullanması gerekir. Önceki kodda her chunk için `embed_query` çağrılıyordu — bu semantik bir hataydı.

### Değişiklikler
- `create_embeddings_one_by_one` → `create_embeddings_batch` olarak yeniden adlandırıldı
- `embed_query` → `embed_documents(batch)` kullanımına geçildi (batch size: 32)
- `progress_callback(current, total)` parametresi eklendi
- Metadata'dan text kaldırıldıktan sonra retrieval bozulduğu için text metadata'ya geri eklendi

```python
def create_embeddings_batch(chunks, embeddings, progress_callback=None, batch_size=32):
    texts = [chunk["text"] for chunk in chunks]
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_vectors = embeddings.embed_documents(batch)
        vectors.extend(batch_vectors)
        if progress_callback:
            progress_callback(min(start + batch_size, len(texts)), len(texts))
    return np.array(vectors, dtype=np.float32)
```

---

## 2. retrieval.py

### Sorunlar
1. `build_faiss_index` içinde gereksiz `faiss.normalize_L2` çağrısı vardı (vektörler zaten normalize)
2. `load_embeddings_and_metadata` içinde gereksiz `.astype("float32")` dönüşümü
3. `simple_tokenize` noktalama işaretlerini kelimelerden ayırmıyordu → BM25 kalitesi düşüktü
4. `retrieve_hybrid` sonuçlarında rank bilgisi hatalı etiketleniyordu (`rrf_ranks` list kullanımı)

### Değişiklikler
- `import re` eklendi
- `faiss.normalize_L2` kaldırıldı
- `simple_tokenize` düzeltildi: `re.sub(r"[^\w\s]", "", text.lower()).split()`
- `faiss_rank` / `bm25_rank` ayrı key'ler olarak saklanmaya başlandı
- **`retrieve_multi_query` eklendi:** Her sub-query için ayrı hybrid retrieval yapıp RRF ile birleştiriyor

```python
def retrieve_multi_query(sub_query_vectors, sub_queries, faiss_index, bm25_index,
                          metadata, top_k=5, rrf_k=60, candidate_k=None):
    # Her sub-query için retrieval → RRF accumulation → top_k döndür
    # Birden fazla sub-query'de geçen chunk'lar daha yüksek skor alır
```

---

## 3. reranking.py

### Sorunlar
- `CrossEncoder` için `max_length` tanımlanmamıştı → uzun metinler sessizce kesiliyordu
- `result["text"]` ile erişim yapılıyordu → key olmadığında `KeyError`

### Değişiklikler
- `CrossEncoder(RERANKER_MODEL_NAME, max_length=512)` — explicit truncation
- `result.get("text", "")` kullanımına geçildi

---

## 4. image_description.py

### Sorunlar & Geliştirmeler
1. Görüntü filtreleme (min boyut, min piksel, min std deviation) kaldırıldı — tüm extract edilen görüntüler işlenmeli
2. GPT-4o çağrıları sıralıydı, paralel değildi — büyük dokümanlarda çok yavaş
3. Paralel çalışmada sıra bozulması riski vardı
4. `max_tokens=1000` yeterliydi → `max_tokens=2000` yapıldı
5. Prompt genel amaçlıydı, RAG için optimize değildi

### Değişiklikler

**Paralel image description:**
```python
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_idx = {
        executor.submit(describe_image_with_gpt, image_path, client): (i, image_path)
        for i, image_path in enumerate(kept)
    }
    # Sıra korundu: results[i] indexed array ile
```

**Geliştirilmiş prompt:**
```
1. IMAGE TYPE: chart / table / diagram / photo / logo / infographic?
2. MAIN CONTENT: Ne iletiliyor?
3. ALL VISIBLE TEXT: Tüm metinler birebir aktarılsın (başlık, etiket, dipnot)
4. DATA & NUMBERS: Tüm sayısal değerler, yüzdeler, tarihler
5. STRUCTURE: Tablo → header/row; grafik → eksen/veri serisi
6. ENTITIES: Organizasyon, kişi, ürün adları
→ Yorumlama değil, direkt aktarım
```

---

## 5. query_processing.py

### Sorunlar
- `create_query_embedding` içinde `faiss.normalize_L2` yapılıyordu (gereksiz)
- Karmaşık çok parçalı sorgular için sub-query desteği yoktu

### Değişiklikler
- `import faiss` ve `faiss.normalize_L2` kaldırıldı
- **`decompose_query_with_gpt` eklendi:**
  - Sorgu tek bir kavramı ele alıyorsa → değiştirmeden döndür
  - Birden fazla bağımsız kavram içeriyorsa → 2-4 atomik sub-query'e böl
  - Temperature: 0.1 (deterministik)

```python
def decompose_query_with_gpt(query, client):
    # "Eğer ayrılmasına gerek yoksa tek query döndür, gerekiyorsa böl"
    # max 4 sub-query, her biri tek kavram
```

- **`create_sub_query_embeddings` eklendi:**
  - Her sub-query için ayrı embedding vektörü döndürür

---

## 6. generation.py

### Sorunlar
- `load_gpt_client` fonksiyonu burada da tanımlıydı (`query_processing.py` ile duplikasyon)
- System prompt zayıftı, strict RAG davranışı için optimize değildi
- `max_tokens` sınırı cevap kalitesini düşürüyordu

### Değişiklikler
- `load_gpt_client` kaldırıldı (tek yer: `query_processing.py`)
- `max_tokens` tamamen kaldırıldı — GPT modelin kendi token sınırına bırakıldı
- **`SYSTEM_PROMPT` yeniden yazıldı** (6 kural):
  1. Sadece context chunk'larındaki bilgiyi kullan
  2. Cevap yoksa: `"The provided documents do not contain..."` döndür
  3. İlgili Chunk ID'lerini kaynak olarak göster
  4. Birden fazla chunk'ı sentezle
  5. Image description chunk'larını normal içerik gibi kullan
  6. Net, doğru ve eksiksiz ol
- Context block'ta `chunk_type != "chunk"` olanlar için tür etiketi eklendi
- Temperature: 0.2

---

## 7. chunking.py

### Geliştirme: Parent Heading Breadcrumb Context

**Sorun:** Sub-section chunk'lar parent başlık context'ini kaybediyordu.

Örnek: `1.1.2 Reporting Lines` chunk'ı embed edilirken `Section: 1.1.2 Reporting Lines` yazılıyordu. Oysa doğrusu `Section: 1. PARENT > 1.1 Sub > 1.1.2 Reporting Lines` olmalıydı.

### Eklenen Fonksiyonlar

**`get_heading_level(line)`** — Başlık hiyerarşi seviyesini döndürür:
| Örnek | Seviye |
|-------|--------|
| `# Başlık` | 1 |
| `## Alt` | 2 |
| `1. Bölüm` | 1 |
| `1.2 Alt` | 2 |
| `1.2.3 Alt-Alt` | 3 |
| `BÜYÜK HARF` | 1 (fallback) |

### `extract_sections` değişiklikleri
- `heading_stack = []` eklendi — `(level, heading_text)` tuple listesi
- Her yeni heading geldiğinde: `level >= current` olan tüm parent'lar stack'ten çıkarılır
- Her section için `breadcrumb` hesaplanır: `"1. Ana > 1.1 Alt > 1.1.2 Detay"`
- Table section'lar için de breadcrumb saklanır

### `chunk_text` değişiklikleri
- `breadcrumb = section.get("breadcrumb", heading)` alınır
- `build_embedded_text` çağrısına `heading` yerine `breadcrumb` verilir
- Metadata'ya `section_breadcrumb` field'ı eklendi (raw `heading` da korunur)

### `merge_small_chunks` değişiklikleri
- Merge edilen chunk'larda `section_breadcrumb` kullanılır

**Sonuç:**
```
Önce: Section: 1.1.2 Reporting Lines
Sonra: Section: 1. PARENT-SUBSIDIARY MODEL > 1.1 Group-Level Decisions > 1.1.2 Reporting Lines
```

---

## 8. main.py

### Multi-Document Upload
- `accept_multiple_files=True` — birden fazla doküman yüklenebilir
- `extracted_texts`, `preprocessed_texts` → `[{filename, text}]` listesi
- Chunking döngüsü: her doküman için ayrı chunk, sequential chunk ID
- Her chunk'ın metadata'sına `source_file` eklendi

### Sub-Query Dekompozsiyonu & Multi-Query Retrieval
- Query expansion sonrası `decompose_query_with_gpt` çağrısı eklendi
- Sub-query'ler UI'da gösteriliyor
- Her sub-query için embedding oluşturuluyor (`create_sub_query_embeddings`)
- Tüm retrieval modları `retrieve_multi_query` kullanıyor
- BM25: `original_query` kullanır, FAISS/Hybrid: expanded query vektörü

### RRF Görüntüleme Düzeltmesi
- `faiss_rank` / `bm25_rank` doğru key'lerle gösteriliyor

### Document Viewer (View in Document)

**Generation page'deki her chunk'ın altında `📄 View in Document` expander'ı eklendi. İçinde kaynak dosya adı, sayfa numarası ve "Open in local viewer" butonu gösteriliyor.**

**Çalışma mantığı — dosya tipine göre:**

**PDF:**
- `fitz` ile orijinal PDF'in geçici bir kopyası oluşturulur
- Chunk'ın `heading` metni + `Content:` kısmındaki tüm satırlar (>15 karakter) target sayfada `page.search_for()` ile aranır
- Bulunan tüm eşleşmelere `page.add_highlight_annot()` ile sarı highlight eklenir
- Chunk birden fazla sayfaya yayılıyorsa `start_page` → `end_page` aralığındaki tüm sayfalarda arama yapılır
- Geçici PDF bir `tempfile` olarak kaydedilir, ayrı bir HTML redirect dosyası ile `file:///tmp.pdf#page=N` adresinde tarayıcıda açılır
- UI bloklanmaması için işlem background thread'de çalışır
- 15 saniye sonra geçici dosyalar silinir — orijinal doküman hiç değişmez

**DOCX / TXT:**
- `os.startfile()` ile varsayılan uygulama (Word, metin editörü) açılır
- Sayfa navigasyonu bu formatlarda mümkün değil, sayfa numarası caption olarak gösterilir

**Image description chunk'ları:**
- PDF yerine `data/images/` altındaki extract edilmiş orijinal görsel `st.image` ile gösterilir

**Highlight arama stratejisi:**
```
search_lines = [heading_text] + [content satırları (>15 karakter)]
her satır için → page.search_for(line) → add_highlight_annot
```

---

## Genel Pipeline Özeti

```
Upload (multi-doc)
    ↓
Ingestion (pdfplumber + fitz + OCR fallback)
    ↓
Preprocessing
    ↓
Chunking (heading-aware recursive + table isolation + parent breadcrumb)
    ↓
Embedding (BGE-M3, embed_documents batch)
    ↓
Image Description (GPT-4o Vision, paralel, structured prompt)
    ↓
Query Expansion (GPT-4o-mini) + Decomposition (sub-queries)
    ↓
Sub-Query Embedding (BGE-M3, embed_query)
    ↓
Multi-Query Retrieval (Hybrid FAISS+BM25, RRF fusion)
    ↓
Reranking (BGE-reranker-v2-m3, CrossEncoder max_length=512)
    ↓
Generation (GPT-4o-mini, strict RAG system prompt)
    ↓
Document Viewer (local PDF açma, #page=N navigation, fitz highlight kopyası)
```
