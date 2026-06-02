# DRAF LAPORAN AKHIR PROYEK
**Mata Kuliah: Rekayasa Perangkat Lunak 2026**  
**Judul Proyek: Agentic AI & Framework Generator (AgentO)**  
**Kelompok: 3**

---

## 1. RINGKASAN PROYEK

### Latar Belakang
Perkembangan teknologi Kecerdasan Buatan berbasis Agen (Agentic AI) telah melahirkan berbagai kerangka kerja (framework) orkestrasi multi-agen populer seperti CrewAI, LangGraph, dan AutoGen. Namun, setiap framework memiliki sintaksis konfigurasi, pola desain, dan manajemen state yang berbeda. Hal ini menimbulkan fragmentasi di mana arsitektur agen yang dirancang secara konseptual harus diterjemahkan secara manual ke dalam kode spesifik framework. Proses translasi manual ini tidak hanya memakan waktu tetapi juga rentan terhadap inkonsistensi struktur dan kesalahan sintaksis. 

Untuk mengatasi masalah tersebut, proyek ini mengembangkan **Agentic AI & Framework Generator (AgentO)**, sebuah sistem generator kode berbasis web semantik. Sistem ini memanfaatkan ontologi formal **AgentO (Agentic AI Ontology)** sebagai sumber kebenaran tunggal (*single source of truth*) dalam memodelkan agen, tugas (tasks), kakas (tools), alur kerja (workflows), dan instruksi prompt.

### Tujuan Utama
1. Membangun mesin generator kode otomatis (*Forward Engineering*) yang dapat mengekstrak spesifikasi arsitektur agen dari file Knowledge Graph (.ttl) berbasis ontologi AgentO menjadi kode Python siap pakai untuk framework CrewAI dan LangGraph.
2. Membangun modul generator balik (*Reverse Engineering*) untuk mengekstraksi kode proyek agen yang sudah ada menjadi representasi Knowledge Graph formal menggunakan bantuan Large Language Model (LLM).
3. Mengembangkan sistem evaluasi kualitas otomatis (*Quality Assurance*) yang mampu menguji validitas sintaksis dan struktur kode yang dihasilkan secara luring (*offline*).

### Ruang Lingkup
- Kerangka kerja target untuk generasi kode: **CrewAI** (pendekatan berbasis YAML untuk konfigurasi agen/tugas dan skrip eksekusi deklaratif) dan **LangGraph** (pendekatan berbasis grafik keadaan dengan 3 pola utama: *Linear*, *Tool-Calling*, dan *Supervisor*).
- File input berupa file serialisasi RDF Turtle (.ttl) yang valid secara semantik berdasarkan skema `agentO.ttl`.
- Validasi kode difokuskan pada analisis statis (AST) dan eksekusi dinamis tiruan (*mock execution*).

### Ringkasan Hasil Akhir
Sistem berhasil diimplementasikan dan dikemas dalam lingkungan Docker. Generator ini mampu memproses **67 skenario Knowledge Graph** yang tersebar di beberapa framework, menghasilkan total lebih dari **2.329 Baris Kode (Lines of Code/LOC)**. Evaluasi kualitas menunjukkan tingkat keberhasilan kompilasi sintaksis mencapai **84,6%** secara akumulatif (100% untuk skenario LangGraph dan 76,5% untuk CrewAI) serta berhasil memvalidasi struktur graph tanpa memerlukan pemanggilan API LLM berbayar.

---

## 2. ARSITEKTUR DAN METODE

### Arsitektur Sistem
Sistem ini menggunakan arsitektur pemrosesan data berbasis pipa (*pipeline*) 3-layer yang terbagi menjadi dua arah rekayasa:

```
A. FORWARD ENGINEERING (Rekayasa Maju)
+------------------------+      SPARQL Query      +-------------------------------+
|  RDF/Turtle (.ttl)     |----------------------->|   Layer 1: Extraction Layer   |
|  Knowledge Graph       |                        |   (Menggunakan RDFLib)        |
+------------------------+                        +-------------------------------+
                                                                  |
                                                                  v
+------------------------+      Jinja2 & YAML     +-------------------------------+
| Python & YAML Project  |<-----------------------|   Layer 3: Generation Layer   |
| (CrewAI / LangGraph)   |                        |   (Pydantic IR -> Codebase)   |
+------------------------+                        +-------------------------------+
                                                                  ^
                                                                  |
                                                  +-------------------------------+
                                                  |   Layer 2: IR Model Layer     |
                                                  |   (Pydantic Data Models)      |
                                                  +-------------------------------+

B. REVERSE ENGINEERING (Rekayasa Balik)
+------------------------+     OpenAI API Call    +-------------------------------+
|  Source Code Proyek    |----------------------->|  LLM (gpt-4o-mini / gpt-5)   |
|  (Python / Config)     |                        |  dengan AgentO Prompt         |
+------------------------+                        +-------------------------------+
                                                                  |
                                                                  v
                                                  +-------------------------------+
                                                  |   RDF Turtle (.ttl)           |
                                                  |   Ontology Instances          |
                                                  +-------------------------------+
```

1. **Layer 1: Extraction Layer (Pengekstrakan Semantik)**
   Menggunakan pustaka `rdflib` untuk membaca file Turtle. Kueri SPARQL dijalankan untuk mengekstrak data agen (peran, deskripsi, model LLM), tugas (deskripsi, output yang diharapkan), tools, node graph, dan relasi transisi (edges).
2. **Layer 2: Intermediate Representation / IR (Representasi Antara)**
   Data mentah hasil ekstraksi SPARQL divalidasi dan dipetakan ke dalam model Pydantic yang terstruktur (`CrewProject`, `LangGraphProject`, `AgentModel`, `TaskModel`, dll.). Layer ini menjamin keamanan tipe data sebelum masuk ke tahap generasi kode.
3. **Layer 3: Generation Layer (Pembangkitan Kode)**
   - **CrewAI**: Membangun konfigurasi terpisah (`agents.yaml` dan `tasks.yaml` menggunakan `PyYAML` aman) serta file logika utama (`crew.py` dan `main.py` menggunakan mesin templat `Jinja2`).
   - **LangGraph**: Menganalisis topologi graph untuk mendeteksi pola orkestrasi (Linear, Tool-Calling, atau Supervisor) dan menyusun grafik keadaan StateGraph berbasis templat Jinja2.

---

## 3. IMPLEMENTASI

### Proses Pembuatan Sistem
Sistem dikembangkan menggunakan bahasa pemrograman Python 3.12 dengan struktur workspace yang bersih dan modular. Kode sumber dibagi menjadi modul generator (`src/`), skrip pengujian & QA (`scripts/`), dataset semantik (`generated_kg/`), dan modul rekayasa balik (`Script/`).

### Modul dan Fitur Utama
1. **Modul CrewAI Generator (`src/crewai/`)**
   - `extractor.py`: Memproses graf RDF dengan SPARQL kustom untuk mengidentifikasi definisi `Agent` dan `Task`.
   - `generator.py`: Merender template Jinja2 untuk menghasilkan file konfigurasi YAML dan kode Python.
   - `run.py`: Runner CLI yang mendukung generasi batch (seluruh dataset) maupun berkas tunggal.
2. **Modul LangGraph Generator (`src/langgraph/`)**
   - `extractor.py`: Mengekstrak topologi node, edge transisi, agen, dan binding tools.
   - `models.py`: Pydantic model yang memiliki logika heuristik (`pattern_type`) untuk mendeteksi pola LangGraph secara otomatis berdasarkan jumlah agen dan ketersediaan tools.
   - `generator.py`: Menyusun kode graph dinamis lengkap dengan definisi state dan transisi kondisional.
3. **Modul Evaluasi Kualitas (`scripts/evaluate_quality.py`)**
   - Menerapkan pipa QA 3-tahap:
     - **Tahap A (Kompilasi Sintaksis)**: Memvalidasi apakah kode Python yang dihasilkan terbebas dari *syntax error* menggunakan modul `py_compile` bawaan Python.
     - **Tahap B (Struktural AST)**: Mem-parsing kode Python menjadi Abstract Syntax Tree (AST) untuk memastikan jumlah fungsi `@tool` dan struktur dekorator agen sesuai dengan metadata pada Pydantic IR.
     - **Tahap C (Eksekusi Runtime Tiruan)**: Mengompilasi dan menginisialisasi grafik keadaan LangGraph secara dinamis di memori dengan menginjeksikan kelas LLM tiruan (`MockChatOpenAI`) untuk mensimulasikan jalannya siklus agen tanpa kuota API asli.
4. **Modul Rekayasa Balik (`Script/run_prompt.py`)**
   - Menggunakan model LLM OpenAI dengan prompt rekayasa semantik (`analysis.prompt.md`) untuk menganalisis kode proyek agen dan menghasilkan output berkas Turtle (.ttl) yang sesuai dengan skema AgentO.

### Integrasi di GitHub Workspace
Repositori dikelola menggunakan sistem kontrol versi Git dengan penamaan branch berbasis fitur. Proyek dikonfigurasi menggunakan file `pyproject.toml` yang kompatibel dengan package manager modern seperti `uv` dan `hatch`. Integrasi Docker dilakukan dengan menyediakan berkas `Dockerfile`, `docker-compose.yml`, dan `entrypoint.sh` sehingga seluruh siklus normalisasi graf, generasi kode, pengujian kualitas, hingga pengumpulan statistik dapat dijalankan dalam satu perintah kontainer tunggal (`docker compose up`).

---

## 4. HASIL EVALUASI

### Metode Pengujian
Pengujian kualitas sistem dilakukan melalui pengujian fungsionalitas otomatis dan analisis statis/dinamis kode. Pengujian terbagi menjadi:
- **Analisis Statis**: Memindai kode Python yang dihasilkan menggunakan modul `ast` untuk mendeteksi ketidaksesuaian struktur.
- **Pengujian Fungsionalitas Offline**: Menjalankan skrip `evaluate_quality.py` untuk menguji fungsionalitas runtime tiruan pada 9 skenario target LangGraph dan 17 skenario CrewAI.

### Metrik dan Hasil Pengujian
Berdasarkan laporan statistik terakhir (`docs/summary_statistics.md` dan `docs/quality_report.md`), berikut adalah hasil evaluasi kualitas sistem:

| Metrik Evaluasi | LangGraph | CrewAI | Total Akumulatif |
|---|:---:|:---:|:---:|
| **Jumlah Skenario Diuji** | 9 | 17 | 26 |
| **Kompilasi Sintaksis (Pass Rate)** | 9/9 (100.0%) | 13/17 (76.5%) | 22/26 (84.6%) |
| **Total Agen yang Dihasilkan** | 8 | 52 | 60 |
| **Total Tugas yang Dihasilkan** | 17 | 60 | 77 |
| **Total Baris Kode (LOC)** | 362 | 1967 | 2329 |
| **Rata-rata Skor Kualitas** | 93.3% | - | - |

*Analisis Skor LangGraph:*
- Seluruh 9 skenario LangGraph lulus uji sintaksis (`py_compile` PASS) dan berhasil dikompilasi ke dalam memori.
- Skor evaluasi struktur dan runtime tiruan mencapai rata-rata **93,3%**. Beberapa skenario mendapatkan skor sempurna (100%) seperti `trip-planner`, `pizza-orderer`, dan `stockbroker`. Reduksi skor pada skenario lainnya diidentifikasi berasal dari ketidaksesuaian penamaan tools semantik akibat namespace IRI yang bocor dari file Turtle.

---

## 5. KENDALA DAN SOLUSI

### Hambatan Teknis dan Solusi
1. **Keterbatasan Kuota dan Biaya API OpenAI saat Evaluasi**
   - *Hambatan*: Pengujian dinamika grafik agen LangGraph membutuhkan pemanggilan LLM. Jika menggunakan API asli OpenAI secara berulang pada puluhan skenario saat pengujian lokal atau CI/CD, biaya API akan membengkak dan rentan terkena limitasi kuota (*rate limits*).
   - *Solusi*: Tim membangun kelas `MockChatOpenAI` dan `MockLLM` dalam pipa evaluasi. Kakas ini meniru respons LLM secara deterministik di memori, memungkinkan grafik keadaan LangGraph untuk melakukan kompilasi `.compile()` dan simulasi transisi node secara luring tanpa biaya API.
2. **Kebocoran IRI Namespace Semantik (IRI Namespace Leakage) pada Ekstraksi Kode**
   - *Hambatan*: Karakter IRI lengkap seperti `http://w3id.org/agentic-ai/onto#extract` sering kali terbawa ke dalam string variabel Python saat parsing RDF. Hal ini mengakibatkan pembuatan nama fungsi Python yang tidak valid (misal: terdapat karakter `/` atau `#`).
   - *Solusi*: Tim mengimplementasikan fungsi normalisasi string kustom pada layer ekstraksi (`extractor.py`). Fungsi ini menggunakan ekspresi reguler (regex) untuk memotong URI dasar dan hanya mengambil bagian fragmen lokal (`localName`), serta memastikan penamaan variabel mematuhi aturan penulisan Python (*snake_case*).
3. **Kompleksitas Perbedaan Orkestrasi Alur Kerja LangGraph**
   - *Hambatan*: Berbeda dengan CrewAI yang sebagian besar berjalan secara linier/sekuensial, LangGraph mendukung alur grafik kompleks. Generator harus mampu memutuskan kapan harus menghasilkan graph linier sederhana, kapan menggunakan model fungsional dengan pemanggilan tools (*tool-calling*), dan kapan harus menyusun struktur supervisor/multi-agent.
   - *Solusi*: Tim membuat properti heuristik `@property def pattern_type` di dalam representasi antara Pydantic (`LangGraphProject`). Properti ini mendeteksi topologi input berdasarkan metrik jumlah agen dan tools secara otomatis, lalu mengarahkan mesin generator untuk menggunakan templat grafik yang sesuai.

---

## 6. KESIMPULAN DAN SARAN

### Kesimpulan
Proyek pengembangan **Agentic AI & Framework Generator (AgentO)** telah berhasil mencapai tujuan utamanya. Pipa generator maju (*Forward Engineering*) mampu mentranslasikan file spesifikasi semantik berbasis RDF/Turtle menjadi kode Python CrewAI dan LangGraph yang dapat dieksekusi secara fungsional. Pipa rekayasa balik (*Reverse Engineering*) berbasis LLM juga terbukti dapat mengekstrak kode sumber agen ke dalam representasi Knowledge Graph secara semi-otomatis. Pengujian otomatis offline yang dikembangkan terbukti sangat efektif dalam menguji integritas kode secara cepat, efisien, dan tanpa dependensi eksternal.

### Saran untuk Pengembangan Mendatang
1. **Perluasan Framework Target**: Menambahkan dukungan generasi kode untuk framework populer lainnya seperti AutoGen secara penuh dan Mastra AI yang saat ini dataset Turtle-nya sudah mulai dikumpulkan.
2. **Peningkatan Skema Validasi**: Mengintegrasikan analisis tipe statis tingkat lanjut (seperti `mypy` atau `ruff`) ke dalam pipeline evaluasi kualitas untuk mendeteksi kesalahan logis atau ketidakcocokan tipe argumen fungsi sejak dini.
3. **Optimalisasi Penanganan State**: Menyediakan mekanisme pemodelan memori agen jangka panjang (*long-term memory*) dan database transisi keadaan graf yang lebih dinamis pada template LangGraph yang dihasilkan.

---

## 7. DOKUMENTASI HASIL PENGERJAAN
*(Bagian ini merupakan placeholder instruksional untuk mempermudah penempelan tangkapan layar / screenshot aplikasi pada berkas Google Docs)*

- **Gambar 1: Struktur Direktori Workspace Proyek**  
  *Deskripsi*: Tangkapan layar yang menampilkan tata letak folder repositori git di VSCode, memperlihatkan folder `src/`, `scripts/`, `Script/`, `generated_kg/`, dan berkas konfigurasi utama (`pyproject.toml`, `requirements.txt`).
- **Gambar 2: Proses Eksekusi Generator Kode Secara Batch**  
  *Deskripsi*: Tangkapan layar terminal setelah menjalankan perintah `python -m src.crewai.run`, menunjukkan log pembacaan graf RDF Turtle dari folder `generated_kg/CrewAI/` dan pembuatan 17 proyek output di dalam folder `output_files/crewai/`.
- **Gambar 3: Struktur Kode Proyek CrewAI yang Dihasilkan**  
  *Deskripsi*: Tangkapan layar berkas hasil generasi untuk salah satu skenario CrewAI (misal: `trip_planner`), menampilkan berkas `config/agents.yaml`, `config/tasks.yaml`, `crew.py`, dan `main.py` yang terstruktur rapi.
- **Gambar 4: Eksekusi Skrip Evaluasi Kualitas Offline**  
  *Deskripsi*: Tangkapan layar terminal yang menampilkan output dari pengoperasian `python scripts/evaluate_quality.py`, menunjukkan tahapan pengujian (Syntax check, Structural AST check, dan Mock runtime) serta tabel ringkasan skor evaluasi kualitas akhir.
- **Gambar 5: Tampilan Jalannya Pipeline Menggunakan Docker Compose**  
  *Deskripsi*: Tangkapan layar terminal saat mengeksekusi kontainerisasi melalui perintah `docker compose up`, menunjukkan siklus lengkap eksekusi kontainer `normalize`, `kickoff`, `generate`, dan `validate` secara sekuensial.

---

## 8. PEMBAGIAN KONTRIBUSI ANGGOTA KELOMPOK

| Nama Anggota | NIM | Peran Utama | Rincian Kontribusi Spesifik |
|---|---|---|---|
| **Kenji Ratanaputra** | 24/534421/PA/22664 | Lead Developer & Integration Engineer | - Merancang struktur proyek dan konfigurasi dasar (`pyproject.toml`).<br>- Mengembangkan modul generator utama untuk framework CrewAI (`src/crewai/`).<br>- Mengintegrasikan template Jinja2 dan modul PyYAML untuk *Forward Engineering* CrewAI.<br>- Mengelola alur kontrol versi git dan sinkronisasi branch utama. |
| **Ayasha Rahmadinni** | 24/545462/PA/23178 | Semantic Engineer | - Menyusun kueri SPARQL untuk ekstraksi data dari graf RDF Turtle.<br>- Mengembangkan modul `extractor.py` baik untuk CrewAI maupun LangGraph.<br>- Menyelesaikan masalah *IRI Namespace Leakage* dengan membuat parser fragmen string lokal.<br>- Melakukan normalisasi berkas-berkas dataset semantik di dalam folder `generated_kg/`. |
| **Kevin Antonio Wiyono Lauw** | 24/535917/PA/22736 | QA & DevOps Engineer | - Membangun modul evaluasi kualitas otomatis (`scripts/evaluate_quality.py`).<br>- Merancang pipa pengujian 3-tahap (Sintaksis, AST structural, dan Mock runtime).<br>- Mengonfigurasi lingkungan Docker (`Dockerfile`, `docker-compose.yml`, dan `entrypoint.sh`).<br>- Menyusun laporan hasil evaluasi (`docs/quality_report.md`) dan analisis bug (`docs/quality_findings.md`). |
| **Melinda Annastasia Budijono** | 24/542840/PA/23052 | Backend & Reverse Engineer | - Mengembangkan logika pemetaan pola orkestrasi LangGraph (Linear, Tool-Calling, Supervisor) pada `src/langgraph/`.<br>- Merancang template kode orkestrasi dinamis LangGraph menggunakan Jinja2.<br>- Mengembangkan mesin rekayasa balik (*Reverse Engineering*) di folder `Script/` menggunakan model LLM OpenAI.<br>- Menyusun dokumentasi panduan repositori (`REPOSITORY_GUIDE.md`) dan draf laporan proyek. |
