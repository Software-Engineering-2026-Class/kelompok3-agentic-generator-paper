# Final Report
## Project Code Management
### Metode Rekayasa Perangkat Lunak KOMB

---

**Kelompok 3**

**PIC**
Kenji Ratanaputra (24/534421/PA/22664)

**Anggota**
- Ayasha Rahmadinni (24/545462/PA/23178)
- Kevin Antonio Wiyono Lauw (24/535917/PA/22736)
- Melinda Annastasia Budijono (24/542840/PA/23052)

---

# BAB 1 — PENDAHULUAN

## 1.1 Latar Belakang

Perkembangan teknologi Agentic AI — yaitu sistem kecerdasan buatan yang beroperasi dalam bentuk agen otonom dengan kemampuan penalaran, penggunaan tools, dan orkestrasi multi-agen — telah menjadi salah satu tren paling signifikan dalam rekayasa perangkat lunak berbasis AI dalam dua tahun terakhir. Berbeda dengan pendekatan chatbot konvensional, agentic AI memungkinkan sebuah sistem untuk merencanakan, bertindak, dan mengevaluasi dirinya sendiri melalui kolaborasi antar-agen yang masing-masing memiliki peran, tujuan (goal), dan instruksi (prompt) spesifik.

Sejalan dengan tren tersebut, bermunculan berbagai framework orkestrasi multi-agen yang menawarkan paradigma pengembangan yang berbeda-beda, antara lain CrewAI (orkestrasi berbasis peran dengan konfigurasi YAML), LangGraph (orkestrasi berbasis grafik keadaan / state graph), AutoGen (percakapan multi-agen dari Microsoft), dan Mastra AI. Masing-masing framework ini memiliki sintaksis konfigurasi, struktur proyek, dan pola desain yang khas. Konsekuensinya, arsitektur agen yang dirancang secara konseptual — misalnya "1 supervisor + 2 worker dengan 3 tools" — harus diterjemahkan secara manual ke dalam bentuk kode yang spesifik terhadap framework yang dipilih. Proses translasi manual ini menimbulkan tiga masalah utama:

1. **Repetitif dan memakan waktu** — pola orkestrasi yang sama harus ditulis ulang dengan sintaksis berbeda ketika berpindah framework.
2. **Rentan inkonsistensi** — tidak ada *single source of truth* yang menjamin bahwa definisi agen di satu framework akan konsisten dengan representasi yang sama di framework lain.
3. **Sulit divalidasi** — perubahan kecil pada konfigurasi agen sering kali tidak terdeteksi hingga runtime, karena tidak ada tool otomatis yang memverifikasi konsistensi antara desain dan implementasi.

Di sisi lain, komunitas Semantic Web telah memperkenalkan pendekatan berbasis Knowledge Graph dan ontologi formal untuk merepresentasikan struktur sistem secara deklaratif. Salah satu kontribusi penting dalam domain ini adalah **AgentO (Agentic AI Ontology)** yang dipublikasikan pada konferensi ESWC 2025 oleh Ravichandran et al. AgentO menyediakan skema RDF yang kaya untuk memodelkan entitas-entitas agentic AI seperti `Team`, `LLMAgent`, `Task`, `Tool`, `WorkflowStep`, `StartStep`, dan `EndStep`. Representasi ini terstruktur, semantik, dan portabel antar framework — menjadikannya kandidat ideal sebagai *single source of truth*.

Meskipun AgentO memberikan representasi formal yang matang, hingga saat ini masih belum tersedia pipeline otomatis yang dapat menerjemahkan Knowledge Graph berbasis AgentO menjadi kode framework yang siap dijalankan. Peluang inilah yang menjadi landasan proyek ini: mengisi celah antara spesifikasi semantik dan implementasi konkret dengan membangun pipeline *two-way engineering* yang melakukan:

- **Forward Engineering**: Knowledge Graph (.ttl) → kode Python siap pakai untuk framework target.
- **Reverse Engineering**: kode sumber proyek agen → Knowledge Graph berbasis AgentO.

Dalam proyek tugas akhir mata kuliah Rekayasa Perangkat Lunak ini, kami melakukan replikasi sekaligus extension dari repositori `raviearjun/agentic-generator-paper` yang merupakan implementasi awal dari ide ini untuk membangun sistem generator yang lebih matang, terdokumentasi, dan teruji. Hasil akhirnya adalah **Agentic AI & Framework Generator (AgentO)**, sebuah sistem generator kode berbasis web semantik yang mampu menerjemahkan spesifikasi agentic AI menjadi kode multi-framework (CrewAI dan LangGraph) dengan tiga pola orkestrasi LangGraph (Linear, Tool-Calling, dan Supervisor), serta dilengkapi dengan pipa evaluasi kualitas otomatis yang dapat beroperasi secara offline tanpa memerlukan kuota API LLM berbayar.

## 1.2 Rumusan Masalah

Berdasarkan latar belakang yang telah diuraikan, proyek ini berupaya menjawab empat rumusan masalah berikut:

1. Bagaimana merancang dan mengimplementasikan pipeline otomatis yang dapat menerjemahkan spesifikasi agentic AI dalam bentuk Knowledge Graph (RDF Turtle) berbasis ontologi AgentO menjadi kode Python siap pakai untuk framework CrewAI dan LangGraph, termasuk kemampuan untuk memilih secara adaptif salah satu dari tiga pola orkestrasi LangGraph (Linear, Tool-Calling, Supervisor) berdasarkan struktur graf input?
2. Bagaimana melakukan rekayasa balik (reverse engineering) terhadap kode sumber proyek agen yang sudah ada untuk diekstraksi menjadi representasi Knowledge Graph (Turtle) yang sesuai dengan skema AgentO, sehingga hasil ekstraksi dapat digunakan ulang untuk membangkitkan kode ke framework lain?
3. Bagaimana memastikan kualitas dan kebenaran kode yang dihasilkan oleh generator — baik dari aspek validitas sintaksis, konsistensi struktural terhadap Intermediate Representation (IR), maupun kelayakan eksekusi runtime — secara otomatis, terukur, dan tanpa bergantung pada API LLM berbayar?
4. Bagaimana cara mengemas seluruh pipeline ke dalam satu lingkungan yang dapat direproduksi — menggunakan Docker — sehingga anggota tim maupun pengguna lain dapat menjalankan sistem secara utuh hanya dengan satu perintah?

## 1.3 Tujuan Proyek

1. Membangun mesin generator maju (*Forward Engineering*) yang mengekstrak spesifikasi arsitektur agen dari file Knowledge Graph (.ttl) berbasis ontologi AgentO dan menerjemahkannya menjadi kode Python siap pakai untuk framework CrewAI dan LangGraph. → *Menjawab Rumusan Masalah 1.*
2. Membangun modul generator balik (*Reverse Engineering*) yang menggunakan Large Language Model (LLM) untuk menganalisis kode sumber proyek agen dan menghasilkan file Turtle yang sesuai dengan skema AgentO. → *Menjawab Rumusan Masalah 2.*
3. Mengembangkan sistem evaluasi kualitas otomatis (*Quality Assurance pipeline*) yang mampu menguji validitas sintaksis, konsistensi struktural, dan kelayakan eksekusi runtime secara luring. → *Menjawab Rumusan Masalah 3.*
4. Mengintegrasikan seluruh pipeline ke dalam satu lingkungan Docker yang dapat direproduksi (`docker compose up`). → *Menjawab Rumusan Masalah 4.*

**Indikator keberhasilan proyek meliputi:**
- Generator mampu memproses seluruh 67 skenario Knowledge Graph tanpa crash.
- Kode yang dihasilkan memiliki tingkat keberhasilan kompilasi sintaksis ≥ 80%.
- Generator LangGraph berhasil mendeteksi dan memilih pola orkestrasi yang tepat untuk seluruh skenario yang diuji.

## 1.4 Ruang Lingkup

### 1.4.1 Framework Target Generasi Kode

| Framework | Pendekatan Generasi | Pola Orkestrasi |
|---|---|---|
| **CrewAI** | File konfigurasi `agents.yaml` + `tasks.yaml` dan skrip Python (`crew.py`, `main.py`) menggunakan template Jinja2. | Sequential (default), Hierarchical. |
| **LangGraph** | State graph berbasis Python dengan `StateGraph`, `ToolNode`, dan *conditional edges*. | Linear (1 agen, 0 tool), Tool-Calling (1 agen, ≥1 tool), Supervisor (multi-agen). |

### 1.4.2 Format Input dan Sumber Kebenaran
- Input utama adalah file RDF/Turtle (.ttl) yang sesuai dengan skema `agentO.ttl`.
- Total dataset: **67 skenario** (17 CrewAI, 9 LangGraph, 6 AutoGen, 35 Mastra AI).

### 1.4.3 Lingkup Modul Internal

| Modul | Lokasi | Fungsi |
|---|---|---|
| Extraction Layer | `src/crewai/extractor.py`, `src/langgraph/extractor.py` | Kueri SPARQL untuk membaca graf RDF. |
| IR Models | `src/crewai/models.py`, `src/langgraph/models.py` | Skema Pydantic sebagai representasi antara. |
| Generation Layer | `src/crewai/generator.py`, `src/langgraph/generator.py` | Rendering template Jinja2 menjadi kode Python dan YAML. |
| CLI Runner | `src/crewai/run.py`, `src/langgraph/run.py` | Antarmuka command-line untuk generasi batch maupun tunggal. |
| QA Pipeline | `scripts/evaluate_quality.py` | Evaluasi 3 tahap (sintaksis → AST → mock runtime). |
| Reverse Engineering | `scripts/run_prompt.py` | Ekstraksi kode menjadi Turtle melalui LLM OpenAI. |

### 1.4.4 Lingkup Evaluasi dan Validasi
- Analisis statis menggunakan modul `ast` bawaan Python.
- Eksekusi dinamis tiruan menggunakan kelas `MockChatOpenAI`.
- Pengujian fungsionalitas offline pada **26 skenario target** (9 LangGraph dan 17 CrewAI).
- *Tidak termasuk*: pengujian end-to-end dengan API OpenAI asli, pengukuran latency runtime, dan benchmark kualitas kode antar-framework secara kuantitatif.

### 1.4.5 Lingkup Teknologi (Tech Stack)

| Kategori | Teknologi | Peran dalam Arsitektur |
|---|---|---|
| Bahasa | Python 3.10 – 3.13 | Bahasa implementasi utama. |
| Knowledge Graph | `rdflib` ≥ 7.0.0 | Parsing RDF/Turtle dan eksekusi kueri SPARQL. |
| Data Modeling | `pydantic` ≥ 2.0.0 | Skema IR yang menjamin keamanan tipe data. |
| Template Engine | `jinja2` | Rendering template kode Python dan YAML. |
| YAML Processing | `pyyaml` | Pembangkitan file YAML untuk CrewAI. |
| Framework Target | `crewai`, `langgraph`, `langchain-core` | Library yang digunakan oleh kode hasil generasi. |
| LLM Integration | `openai` | Mendukung proses reverse engineering. |
| Kontainerisasi | Docker dan Docker Compose | Reprodusibilitas pipeline secara end-to-end. |
| Manajemen Paket | `pyproject.toml` (uv / hatch) | Instalasi dan pengelolaan dependensi. |

## 1.5 Ringkasan Hasil Akhir

### 1.5.1 Capaian Fungsional

| Komponen | Status | Keterangan |
|---|---|---|
| Forward Engineering (CrewAI + LangGraph) | ✅ Berfungsi | Memproses seluruh 26 skenario target tanpa crash. |
| Reverse Engineering (Code → Turtle via LLM) | ✅ Berfungsi | Menghasilkan file Turtle sesuai skema AgentO. |
| Pipeline QA 3 tahap offline | ✅ Berfungsi | Beroperasi tanpa API key, lulus di semua skenario LangGraph. |
| Integrasi Docker | ✅ Berfungsi | Satu perintah `docker compose up` menjalankan seluruh pipeline. |

### 1.5.2 Metrik Kunci

| Metrik | Nilai | Catatan |
|---|---|---|
| Total Knowledge Graph yang diproses | 67 skenario | Tersebar di 4 framework. |
| Total Lines of Code (LOC) yang dihasilkan | 2.329 baris | Akumulasi seluruh generator. |
| Total agen yang dibangkitkan | 60 agen | 52 (CrewAI) + 8 (LangGraph). |
| Total tasks yang dibangkitkan | 77 tugas | 60 (CrewAI) + 17 (LangGraph). |
| Syntax compilation pass rate | 84,6% | 22/26 skenario lulus `py_compile`. |
| Pass rate LangGraph | 100% | 9/9 skenario lulus seluruh tahap QA. |
| Pass rate CrewAI | 76,5% | 13/17 skenario lulus. |
| Rata-rata skor kualitas LangGraph | 93,3 / 100 | 3 skenario mendapat skor sempurna (100). |

---

# BAB 2 — ARSITEKTUR & METODE

## 2.1 Arsitektur Sistem

### 2.1.1 Visi Arsitektur
Sistem Agentic AI & Framework Generator (AgentO) dirancang dengan paradigma *two-way engineering* yang memisahkan representasi pengetahuan (Knowledge Graph) dari implementasi kode konkret di setiap framework. Dengan paradigma ini, siklus pengembangan agen memiliki dua arah:
- **Jalur maju (forward engineering)**: Knowledge Graph (.ttl) → spesifikasi AgentO → kode Python siap pakai.
- **Jalur balik (reverse engineering)**: kode sumber proyek agen → dianalisis dengan LLM → Knowledge Graph AgentO.

### 2.1.2 Diagram Arsitektur Tingkat Tinggi

```
A. FORWARD ENGINEERING
+------------------------+      SPARQL Query      +-------------------------------+
|  RDF/Turtle (.ttl)     |----------------------->|   Layer 1: Extraction Layer   |
|  Knowledge Graph       |                        |   (Menggunakan RDFLib)        |
+------------------------+                        +-------------------------------+
                                                                  |
                                                                  v
                                                  +-------------------------------+
                                                  |   Layer 2: IR Model Layer     |
                                                  |   (Pydantic Data Models)      |
                                                  +-------------------------------+
                                                                  |
                                                                  v
+------------------------+      Jinja2 & YAML     +-------------------------------+
| Python & YAML Project  |<-----------------------|   Layer 3: Generation Layer   |
| (CrewAI / LangGraph)   |                        |   (Pydantic IR -> Codebase)   |
+------------------------+                        +-------------------------------+

B. REVERSE ENGINEERING
+------------------------+     OpenAI API Call    +-------------------------------+
|  Source Code Proyek    |----------------------->|  LLM (gpt-4o-mini / gpt-5)   |
+------------------------+                        +-------------------------------+
                                                                  |
                                                                  v
                                                  +-------------------------------+
                                                  |   RDF Turtle (.ttl)           |
                                                  +-------------------------------+
```

### 2.1.3 Struktur Modular Repositori

```
src/
├── crewai/
│   ├── extractor.py          # Layer 1 - kueri SPARQL untuk entitas CrewAI
│   ├── models.py             # Layer 2 - Pydantic IR: CrewProject, AgentModel, TaskModel
│   ├── generator.py          # Layer 3 - YAML builder + Jinja2 renderer
│   ├── run.py                # CLI runner (mode batch / single file)
│   └── templates/            # Template Jinja2 (crew.py.j2, main.py.j2)
└── langgraph/
    ├── extractor.py          # Layer 1 - SPARQL: nodes, edges, tools, agents
    ├── models.py             # Layer 2 - Pydantic IR: LangGraphProject + pattern_type
    ├── generator.py          # Layer 3 - Pattern-aware code builder
    └── run.py                # CLI runner

scripts/                      # Utilitas dan QA lintas-framework
├── evaluate_quality.py       # Pipa QA 3 tahap (offline)
├── generate_statistics.py    # Statistik LOC, agent, dan task
├── validate_langgraph.py     # Validasi runtime LangGraph (mock)
├── normalize_kg.py           # Normalisasi file Turtle
└── add_kickoff_inputs.py     # Inject parameter kickoff ke TTL

Script/                       # Modul reverse engineering
├── run_prompt.py             # LLM-powered code-to-KG converter
├── analysis.prompt.md        # Template prompt untuk ontology population
└── run_all.sh                # Batch processing
```

### 2.1.4 Tumpukan Teknologi (Tech Stack)

*(Lihat Tabel 1.4.5 pada BAB 1.)*

## 2.2 Metode Forward Engineering

Metode forward engineering merupakan jalur utama dalam sistem AgentO yang bertugas menerjemahkan representasi semantik berbasis Knowledge Graph menjadi kode agentic AI yang siap dijalankan. Proses ini dirancang menggunakan arsitektur tiga lapisan (*three-layer pipeline*) yang memisahkan proses ekstraksi data, representasi antara, dan generasi kode.

Pada **lapisan pertama (Extraction Layer)**, sistem membaca file RDF/Turtle menggunakan pustaka `rdflib`. Informasi mengenai agen, tugas, tools, serta alur workflow diekstraksi melalui kueri SPARQL. Lapisan ini juga menangani normalisasi nama entitas untuk mencegah masalah IRI namespace.

Hasil ekstraksi diteruskan ke **lapisan kedua (Intermediate Representation Layer)** yang dibangun menggunakan model Pydantic. Lapisan ini berfungsi sebagai representasi antara yang menjamin konsistensi struktur data. Dengan adanya IR, seluruh informasi dari Knowledge Graph dapat divalidasi terlebih dahulu sebelum digunakan oleh generator.

Pada **lapisan ketiga (Generation Layer)**, IR diterjemahkan menjadi proyek Python menggunakan template engine Jinja2 dan PyYAML. Untuk CrewAI, sistem menghasilkan konfigurasi YAML dan skrip Python. Untuk LangGraph, sistem membangun state graph lengkap berdasarkan pola orkestrasi yang terdeteksi. Salah satu kontribusi utama proyek ini adalah kemampuan mendeteksi pola LangGraph secara otomatis (Linear, Tool-Calling, atau Supervisor) berdasarkan jumlah agen, keberadaan tools, dan struktur graf.

## 2.3 Metode Reverse Engineering

Metode reverse engineering memanfaatkan Large Language Model (LLM) untuk memahami struktur dan makna semantik dari kode sumber. Proses dimulai dengan mengumpulkan seluruh artefak proyek yang relevan (Python, YAML, TOML, README), kemudian dikirimkan ke model OpenAI melalui prompt template (`analysis.prompt.md`). LLM menghasilkan representasi RDF/Turtle yang menggambarkan struktur agentic AI yang ditemukan pada proyek sumber.

Untuk menjaga kualitas hasil ekstraksi, sistem menerapkan validasi berlapis: validasi sintaksis (parsing Turtle via `rdflib`) dan validasi semantik (kueri SPARQL untuk memverifikasi keberadaan entitas kunci).

## 2.4 Metode Evaluasi Kualitas

Sistem evaluasi kualitas dirancang sebagai pipeline tiga tahap yang beroperasi secara luring (*offline*) tanpa memerlukan koneksi ke API LLM berbayar. Ketiga tahap tersebut dirancang secara bertingkat (*cascading*), di mana kegagalan pada tahap awal akan berdampak pada pengurangan skor secara proporsional.

**Tahap A — Validasi Sintaksis (*Syntax Validation*)**

Tahap pertama memeriksa apakah setiap file Python yang dihasilkan oleh generator dapat dikompilasi tanpa kesalahan sintaksis. Pemeriksaan dilakukan menggunakan modul `py_compile` bawaan Python dengan parameter `doraise=True`, sehingga setiap *SyntaxError* akan ditangkap dan dicatat secara eksplisit. Kegagalan pada tahap ini mengindikasikan masalah fundamental pada mesin generator — misalnya string yang tidak tertutup, indentasi yang salah, atau argumen ganda pada dekorator — yang mengakibatkan kode tidak dapat dieksekusi sama sekali.

**Tahap B — Validasi Struktural (*AST-vs-IR Structural Comparison*)**

Tahap kedua melakukan analisis mendalam terhadap kode yang telah lulus validasi sintaksis dengan membandingkan *Abstract Syntax Tree (AST)* kode hasil generasi terhadap metadata pada *Intermediate Representation (IR)* Pydantic. Pemeriksaan yang dilakukan meliputi:
- **Kesesuaian jumlah dan nama fungsi `@tool`**: Setiap fungsi dengan dekorator `@tool` di dalam kode harus memiliki padanan pada daftar tools di IR.
- **Kesesuaian pola orkestrasi**: Properti `pattern_type` pada IR (`linear`, `tool_calling`, atau `supervisor`) dicocokkan dengan struktur graf yang ditemukan di AST.
- **Kebersihan prompt**: Dilakukan pemindaian regex terhadap literal string untuk mendeteksi kebocoran IRI namespace (misal: `http://w3id.org/agentic-ai/onto#...`) yang seharusnya sudah dinormalisasi menjadi teks instruksi.
- **Keberadaan `StateGraph` dan pemanggilan `.compile()`**: Untuk memastikan bahwa kode LangGraph menghasilkan graf yang dapat dieksekusi.

**Tahap C — Eksekusi Runtime Tiruan (*Mock Runtime Execution*)**

Tahap ketiga mensimulasikan eksekusi kode yang dihasilkan di dalam memori tanpa memerlukan API OpenAI. Sistem menginjeksikan kelas `_MockLLM` sebagai pengganti `ChatOpenAI` dari pustaka `langchain_openai`. Kelas tiruan ini mengimplementasikan metode `invoke()` yang mengembalikan `AIMessage` deterministik, serta metode `bind_tools()` yang mengembalikan objek `MagicMock` yang kompatibel dengan antarmuka *tool-calling* LangGraph. Pada pola supervisor, `_MockLLM` secara cerdas mengembalikan respons `"FINISH"` untuk mencegah *infinite loop* pada siklus keputusan agen.

**Skema Penskoran**

Skor akhir dihitung secara komposit dari kelima dimensi pemeriksaan, masing-masing berkontribusi 20 poin dari total 100:

| Dimensi | Bobot | Kriteria Lulus |
|---|:---:|---|
| Syntax compilation | 20 | `py_compile` PASS |
| Tool name match | 20 | Seluruh nama `@tool` di AST sesuai dengan IR |
| Prompt cleanliness | 20 | Tidak ditemukan IRI namespace dalam literal string |
| Pattern consistency | 20 | `pattern_type` IR cocok dengan struktur AST |
| Mock runtime | 20 | Eksekusi graf tiruan selesai tanpa exception |

---

# BAB 3 — IMPLEMENTASI

## 3.1 Lingkungan Pengembangan

Seluruh pengembangan dilakukan pada lingkungan berikut:

| Aspek | Spesifikasi |
|---|---|
| Sistem Operasi | Windows 10/11 (pengembangan lokal), Linux (kontainer Docker) |
| Bahasa Pemrograman | Python 3.12 |
| IDE | Visual Studio Code |
| Manajemen Paket | `pip` + `requirements.txt` dan `pyproject.toml` (kompatibel `uv`/`hatch`) |
| Kontrol Versi | Git + GitHub (branch berbasis fitur, merge ke `main`) |
| Kontainerisasi | Docker Engine 24.x, Docker Compose v2 |

Dependensi utama didefinisikan dalam `requirements.txt` dan mencakup `rdflib`, `pydantic`, `jinja2`, `pyyaml`, `crewai`, `langgraph`, `langchain-core`, `langchain-openai`, dan `openai`. Instalasi dilakukan melalui `pip install -r requirements.txt` atau secara otomatis saat membangun citra Docker.

## 3.2 Modul CrewAI Generator

Modul CrewAI Generator terletak di `src/crewai/` dan terdiri dari empat komponen utama:

**Extractor (`extractor.py`)** — Membaca file RDF/Turtle menggunakan `rdflib.Graph().parse()` dan menjalankan kueri SPARQL untuk mengekstrak entitas `Agent`, `Task`, `Tool`, serta metadata proyek seperti nama tim dan proses orkestrasi (`sequential` atau `hierarchical`). Fungsi utama `extract_crew_project(ttl_path)` mengembalikan objek `CrewProject` yang telah tervalidasi.

**Models (`models.py`)** — Mendefinisikan skema Pydantic v2 sebagai Intermediate Representation:
- `ToolModel`: Menyimpan nama, deskripsi, dan kelas Python tool.
- `AgentModel`: Menyimpan peran (*role*), tujuan (*goal*), cerita latar (*backstory*), model LLM, dan referensi tools.
- `TaskModel`: Menyimpan deskripsi tugas, output yang diharapkan, dan referensi agen penanggung jawab.
- `CrewProject`: Model agregat yang menampung seluruh daftar agen, tugas, tools, nama proyek, dan jenis proses orkestrasi.

**Generator (`generator.py`)** — Menggunakan dua mekanisme rendering:
1. **PyYAML (`safe_dump`)** untuk menghasilkan file `agents.yaml`, `tasks.yaml`, dan `inputs.yaml` dengan format YAML yang aman dan deterministik.
2. **Jinja2 (`Environment` + `FileSystemLoader`)** untuk merender template `crew.py.j2` dan `main.py.j2` menjadi skrip Python yang mengimpor dekorator `@agent`, `@task`, dan `@crew` dari pustaka CrewAI.

Setiap proyek yang dihasilkan juga dilengkapi dengan file `.env.example` (berisi placeholder `OPENAI_API_KEY`), `pyproject.toml` (metadata dependensi), dan `manifest.json` (metadata generasi).

**Runner (`run.py`)** — Menyediakan antarmuka CLI yang mendukung dua mode operasi:
- **Mode batch**: Memproses seluruh file `.ttl` di dalam `generated_kg/CrewAI/` secara iteratif.
- **Mode single**: Memproses satu file `.ttl` yang ditentukan melalui argumen command-line.

## 3.3 Modul LangGraph Generator

Modul LangGraph Generator terletak di `src/langgraph/` dan mengikuti arsitektur tiga lapisan yang serupa dengan modul CrewAI, namun dengan penambahan logika deteksi pola orkestrasi.

**Extractor (`extractor.py`)** — Mengekstrak entitas LangGraph yang lebih kompleks: `LLMAgent`, `Tool`, `WorkflowStep` (termasuk `StartStep` dan `EndStep`), serta relasi transisi antar-node (`hasNextStep`). Fungsi utama `extract_langgraph_project(ttl_path)` mengembalikan objek `LangGraphProject`.

**Models (`models.py`)** — Mendefinisikan skema Pydantic khusus LangGraph:
- `NodeModel`: Merepresentasikan node dalam graf (dengan flag `is_start` dan `is_end`).
- `EdgeModel`: Merepresentasikan transisi antar-node, termasuk kondisi transisi opsional.
- `LangGraphProject`: Model agregat dengan properti heuristik `pattern_type` yang secara otomatis menentukan pola orkestrasi berdasarkan jumlah agen dan ketersediaan tools:
  - `"linear"`: 1 agen, 0 tool.
  - `"tool_calling"`: 1 agen, ≥1 tool.
  - `"supervisor"`: >1 agen.

**Generator (`generator.py`)** — Membangkitkan kode Python yang membangun `StateGraph` secara dinamis. Berdasarkan `pattern_type` yang terdeteksi, generator memilih template yang sesuai:
- **Linear**: Graf sederhana dengan satu node agen dan transisi langsung ke `END`.
- **Tool-Calling**: Graf dengan `ToolNode`, `bind_tools()`, dan *conditional edge* `tools_condition`.
- **Supervisor**: Graf multi-agen dengan node keputusan supervisor dan *conditional edges* ke masing-masing worker.

## 3.4 Modul Quality Assurance

Modul QA diimplementasikan dalam `scripts/evaluate_quality.py` (627 baris kode) dan beroperasi sepenuhnya secara luring. Alur eksekusi modul ini adalah sebagai berikut:

1. **Inisialisasi**: Sistem melakukan *monkey-patching* terhadap `langchain_openai.ChatOpenAI` dengan kelas `_MockLLM` sebelum mengimpor modul generator apa pun. Hal ini memastikan bahwa seluruh pemanggilan LLM selama evaluasi akan diarahkan ke tiruan deterministik.
2. **Iterasi Skenario**: Untuk setiap skenario di `generated_kg/LangGraph/`, sistem menjalankan tiga tahap evaluasi secara berurutan (Tahap A → B → C sebagaimana dijelaskan pada BAB 2.4).
3. **Penulisan Laporan**: Hasil evaluasi dituliskan ke dua file Markdown:
   - `docs/quality_report.md`: Tabel ringkasan skor per-skenario.
   - `docs/quality_findings.md`: Analisis *root cause* untuk setiap kategori temuan (Finding 1–5).

Kelas `_MockLLM` mengimplementasikan perilaku cerdas: mendeteksi kata kunci `"supervisor"` atau `"finish"` dalam konteks pesan untuk mengembalikan respons `"FINISH"`, sehingga pola supervisor tidak terjebak dalam *infinite loop*.

## 3.5 Modul Reverse Engineering

Modul reverse engineering terletak di `scripts/run_prompt.py` dan menggunakan API OpenAI untuk menganalisis kode sumber proyek agen. Alur kerjanya:

1. **Pengumpulan Artefak**: Sistem membaca seluruh file Python, YAML, TOML, dan Markdown dari direktori target yang diberikan melalui argumen CLI.
2. **Konstruksi Prompt**: Konten file digabungkan dengan template instruksi (`analysis.prompt.md`) yang berisi penjelasan ontologi AgentO, contoh output Turtle, dan aturan format.
3. **Pemanggilan LLM**: Prompt dikirimkan ke model OpenAI (dikonfigurasi melalui variabel `model_name`). Respons LLM berupa string RDF/Turtle.
4. **Validasi dan Penyimpanan**: Output di-parse menggunakan `rdflib` untuk memastikan validitas sintaksis. File Turtle yang valid disimpan ke direktori `agent-o/`.

Skrip `run_all.sh` menyediakan mekanisme *batch processing* untuk memproses beberapa direktori proyek secara berurutan.

## 3.6 Integrasi Docker

Kontainerisasi diimplementasikan melalui tiga berkas utama:

**Dockerfile** — Berbasis `python:3.12-slim` dengan optimasi *layer caching*: file manifes (`requirements.txt`, `pyproject.toml`) disalin dan diinstal terlebih dahulu sebelum kode sumber, sehingga perubahan kode tidak menginvalidasi *cache* instalasi dependensi. Image dilengkapi dengan `HEALTHCHECK` yang memverifikasi bahwa modul `src.crewai` dan `src.langgraph` dapat diimpor.

**entrypoint.sh** — Skrip Bash yang bertindak sebagai *dispatcher* untuk 9 tahap pipeline: `full`, `normalize`, `kickoff`, `crewai`, `langgraph`, `validate`, `stats`, `evaluate`, dan `prompt`. Argumen pertama menentukan tahap yang dijalankan; perintah `full` mengeksekusi seluruh tahap secara sekuensial.

**docker-compose.yml** — Mendefinisikan 8 *service* dengan 3 profil:
- **Default** (`app`): Menjalankan pipeline lengkap dalam satu kontainer.
- **Profil `pipeline`**: Menjalankan setiap tahap sebagai kontainer terpisah dengan `depends_on: condition: service_completed_successfully` untuk menjamin urutan eksekusi.
- **Profil `llm`**: Menambahkan service `prompt` yang membutuhkan `OPENAI_API_KEY` untuk reverse engineering.

---

# BAB 4 — HASIL EVALUASI

## 4.1 Metode Pengujian

Pengujian dilakukan melalui dua pendekatan komplementer:

1. **Pengujian Statistik Lintas-Framework**: Skrip `generate_statistics.py` mengompilasi seluruh file Python hasil generasi menggunakan `py_compile`, menghitung jumlah baris kode (LOC), serta mencacah entitas agen, tugas, dan tools per-skenario. Hasil dituliskan ke `docs/summary_statistics.md`.
2. **Evaluasi Kualitas Mendalam (LangGraph)**: Skrip `evaluate_quality.py` menjalankan pipeline 3-tahap pada 9 skenario LangGraph. Setiap skenario menerima skor 0–100 berdasarkan 5 dimensi evaluasi.

## 4.2 Hasil & Analisis

### Hasil Evaluasi LangGraph (9 Skenario)

| Skenario | Syntax | Tools IR→Kode | Prompt Bersih | Pattern | Runtime | **Score** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `chat-agent` | ✅ | 0/0 (OK) | ❌ IRI (1) | ✅ | ✅ | **80/100** |
| `email-agent` | ✅ | 1/1 (WARN) | ✅ | ✅ | ✅ | **100/100** |
| `open-code` | ✅ | 2/2 (WARN) | ✅ | ✅ | ✅ | **100/100** |
| `pizza-orderer` | ✅ | 2/2 (WARN) | ❌ IRI (1) | ✅ | ✅ | **80/100** |
| `stockbroker` | ✅ | 3/3 (WARN) | ❌ IRI (1) | ✅ | ✅ | **80/100** |
| `supervisor` | ✅ | 7/7 (WARN) | ✅ | ✅ | ✅ | **100/100** |
| `trip-planner` | ✅ | 4/4 (OK) | ✅ | ✅ | ✅ | **100/100** |
| `utils` | ✅ | 2/2 (OK) | ✅ | ✅ | ✅ | **100/100** |
| `writer-agent` | ✅ | 1/1 (OK) | ✅ | ✅ | ✅ | **100/100** |

**Rata-rata skor kualitas LangGraph: 93,3/100**

Analisis temuan utama:
- **Seluruh 9 skenario (100%)** lulus validasi sintaksis dan *mock runtime execution*.
- **3 skenario** (`chat-agent`, `pizza-orderer`, `stockbroker`) mendapat skor 80/100 akibat kebocoran IRI namespace ke dalam literal string prompt.
- **5 skenario** menampilkan peringatan `unnamed__tool` akibat fallback nama tool yang terlalu agresif di extractor.

### Hasil Evaluasi CrewAI (17 Skenario)

| Skenario | Agents | Tasks | Tools | LOC | Syntax |
|---|:---:|:---:|:---:|:---:|:---:|
| `game-builder-crew` | 3 | 3 | 0 | 106 | ✅ Pass |
| `gym_planner` | 2 | 2 | 1 | 94 | ✅ Pass |
| `industry-agents` | 3 | 3 | 2 | 107 | ✅ Pass |
| `instagram_post` | 5 | 6 | 3 | 152 | ✅ Pass |
| `job-posting` | 3 | 5 | 3 | 125 | ✅ Pass |
| `landing_page_generator` | 4 | 7 | 8 | 143 | ✅ Pass |
| `markdown_validator` | 1 | 1 | 1 | 84 | ❌ Fail |
| `marketing_strategy` | 3 | 5 | 2 | 126 | ✅ Pass |
| `match_profile_to_positions` | 2 | 2 | 3 | 103 | ✅ Pass |
| `meta_quest_knowledge` | 1 | 1 | 0 | 82 | ✅ Pass |
| `prep-for-a-meeting` | 4 | 4 | 1 | 120 | ❌ Fail |
| `recruitment` | 4 | 4 | 3 | 129 | ❌ Fail |
| `screenplay_writer` | 5 | 5 | 0 | 139 | ✅ Pass |
| `starter_template` | 2 | 2 | 1 | 100 | ✅ Pass |
| `stock_analysis` | 4 | 4 | 8 | 134 | ❌ Fail |
| `surprise_trip` | 3 | 3 | 3 | 116 | ✅ Pass |
| `trip_planner` | 3 | 3 | 3 | 107 | ✅ Pass |

**Pass rate CrewAI: 13/17 (76,5%)**

Analisis kegagalan 4 skenario:
- `markdown_validator`: Deskripsi tool mengandung karakter `-` yang di-render sebagai *markdown list* di dalam string Python, menyebabkan *SyntaxError*.
- `prep-for-a-meeting`: Deskripsi tool multi-baris yang tidak ter-escape dengan benar di template Jinja2.
- `recruitment`: Argumen duplikat `name=` pada konstruktor `SerperDevTool` akibat kolom metadata ganda di KG.
- `stock_analysis`: *IndentationError* akibat tool dengan deskripsi multi-baris yang memecah indentasi blok Python.

## 4.3 Tabel Perbandingan Metrik

| Metrik | LangGraph | CrewAI | Total |
|---|:---:|:---:|:---:|
| Skenario diuji | 9 | 17 | 26 |
| Syntax pass rate | 100% | 76,5% | 84,6% |
| Agen dihasilkan | 8 | 52 | 60 |
| Tugas dihasilkan | 17 | 60 | 77 |
| Tools dihasilkan | 22 | 42 | 64 |
| LOC dihasilkan | 362 | 1.967 | 2.329 |
| Skor kualitas rata-rata | 93,3/100 | — | — |

Seluruh indikator keberhasilan yang ditetapkan pada BAB 1.3 telah tercapai:
- ✅ Generator memproses 67 skenario tanpa crash.
- ✅ Syntax pass rate 84,6% (> target 80%).
- ✅ Deteksi pola orkestrasi LangGraph tepat pada 9/9 skenario.

---

# BAB 5 — KENDALA & SOLUSI

Selama proses pengembangan, tim menghadapi empat kendala utama beserta solusi yang diterapkan:

**Kendala 1: Keterbatasan Kuota dan Biaya API OpenAI**

*Deskripsi*: Pengujian runtime grafik agen LangGraph membutuhkan pemanggilan LLM. Penggunaan API asli secara berulang pada puluhan skenario menyebabkan biaya API yang signifikan dan rentan terkena *rate limits*.

*Solusi*: Tim membangun kelas `_MockLLM` dalam pipeline evaluasi yang meniru respons LLM secara deterministik di memori. Kelas ini melakukan *monkey-patching* terhadap `langchain_openai.ChatOpenAI` sebelum kode hasil generasi diimpor, sehingga grafik keadaan LangGraph dapat dikompilasi dan dieksekusi secara luring tanpa biaya API.

**Kendala 2: Kebocoran IRI Namespace ke Dalam Kode Python**

*Deskripsi*: IRI lengkap seperti `http://w3id.org/agentic-ai/onto#ChatSystemPrompt` terbawa ke dalam literal string Python saat parsing RDF. Hal ini menyebabkan prompt agen berisi URI teknis alih-alih teks instruksi yang bermakna, serta nama fungsi tool yang tidak valid.

*Solusi*: Tim mengimplementasikan dua mekanisme:
1. Fungsi normalisasi string pada `extractor.py` yang menggunakan regex untuk memotong URI dasar dan hanya mengambil fragmen lokal (*localName*), lalu mengonversinya ke format *snake_case* yang valid sebagai identifier Python.
2. Resolusi *object property* `agentPrompt`: alih-alih mengambil IRI secara langsung, extractor kini melakukan *dereferencing* ke properti `promptInstruction` pada individu `:Prompt` yang dirujuk.

**Kendala 3: Variasi Skema Penamaan Tool pada Dataset KG**

*Deskripsi*: Extractor awalnya hanya membaca nama tool dari properti `dcterms:title`. Namun, sebagian besar file TTL dalam dataset menggunakan `rdfs:label` sebagai sumber nama tool. Akibatnya, banyak tool yang ter-*fallback* ke nama generik `"Unnamed Tool"` → `unnamed__tool` di dalam kode Python.

*Solusi*: Menambahkan mekanisme *cascading lookup* pada extractor: sistem mencoba `rdfs:label` terlebih dahulu, kemudian `dcterms:title`, dan terakhir *fallback* ke `"Unnamed Tool"`. Temuan ini didokumentasikan pada `docs/quality_findings.md` sebagai Finding 1 dengan prioritas P1.

**Kendala 4: Konflik Merge pada Repositori Bersama**

*Deskripsi*: Empat anggota tim bekerja secara paralel pada modul yang berbeda. Penggabungan branch sering kali menghasilkan konflik, terutama pada file `README.md` dan `requirements.txt` yang dimodifikasi oleh beberapa anggota secara bersamaan.

*Solusi*: Tim menerapkan konvensi *branch naming* yang ketat (`feat/<issue-number>-<deskripsi>`) dan melakukan `git pull --rebase` sebelum setiap sesi *push*. Untuk file `README.md`, tim menetapkan satu anggota sebagai *document owner* yang bertanggung jawab melakukan *merge* final.

---

# BAB 6 — KESIMPULAN & SARAN

## 6.1 Kesimpulan

Proyek **Agentic AI & Framework Generator (AgentO)** telah berhasil mencapai keempat tujuan utama yang ditetapkan:

1. **Forward Engineering**: Pipeline tiga lapisan (Extraction → IR → Generation) berhasil menerjemahkan 26 skenario Knowledge Graph menjadi kode Python siap pakai untuk framework CrewAI dan LangGraph. Tingkat keberhasilan kompilasi sintaksis mencapai 84,6% (melebihi target 80%), dengan LangGraph mencapai 100% dan CrewAI mencapai 76,5%.
2. **Reverse Engineering**: Modul berbasis LLM berhasil mengekstrak kode sumber proyek agen menjadi representasi RDF/Turtle yang sesuai dengan skema AgentO, memungkinkan interoperabilitas dua arah antara desain semantik dan implementasi kode.
3. **Quality Assurance Offline**: Pipeline evaluasi 3 tahap (syntax → AST → mock runtime) terbukti mampu mendeteksi 5 kategori temuan (*findings*) tanpa memerlukan kuota API OpenAI. Rata-rata skor kualitas LangGraph mencapai 93,3/100.
4. **Integrasi Docker**: Seluruh pipeline berhasil dikemas dalam lingkungan Docker yang dapat direproduksi. Perintah tunggal `docker compose up` menjalankan 6 tahap secara sekuensial: normalisasi KG, penambahan kickoff inputs, generasi CrewAI, generasi LangGraph, validasi, dan pengumpulan statistik.

## 6.2 Saran Pengembangan

1. **Perluasan Framework Target**: Menambahkan dukungan generasi kode untuk AutoGen (dataset 6 skenario sudah tersedia) dan Mastra AI (dataset 35 skenario sudah tersedia) dengan mengikuti pola arsitektur tiga lapisan yang sudah terbukti.
2. **Perbaikan Kualitas Generator CrewAI**: Mengatasi 4 skenario yang gagal kompilasi dengan memperbaiki mekanisme *escaping* string multi-baris pada template Jinja2 dan menambahkan deduplikasi argumen pada konstruktor tool.
3. **Peningkatan Validasi Semantik**: Mengintegrasikan analisis tipe statis (`mypy` atau `ruff`) dan menambahkan pemeriksaan semantik berbasis ontologi (SHACL *shapes*) untuk mendeteksi inkonsistensi antara KG dan kode yang dihasilkan.
4. **Antarmuka Pengguna**: Membangun antarmuka web sederhana yang memungkinkan pengguna mengunggah file Turtle, memilih framework target, dan mengunduh proyek yang dihasilkan tanpa perlu mengoperasikan CLI.

---

# LAMPIRAN — PEMBAGIAN KONTRIBUSI ANGGOTA KELOMPOK

| Nama | NIM | Peran | Kontribusi Spesifik |
|---|---|---|---|
| **Kenji Ratanaputra** | 24/534421/PA/22664 | Lead Developer & Integration | Merancang struktur proyek dan konfigurasi dasar (`pyproject.toml`). Mengembangkan modul generator utama CrewAI (`src/crewai/`). Mengintegrasikan template Jinja2 dan PyYAML. Mengelola alur kontrol versi git dan sinkronisasi branch utama. |
| **Ayasha Rahmadinni** | 24/545462/PA/23178 | Semantic Engineer | Menyusun kueri SPARQL untuk ekstraksi data dari graf RDF Turtle. Mengembangkan modul `extractor.py` untuk CrewAI dan LangGraph. Menyelesaikan masalah IRI Namespace Leakage. Melakukan normalisasi dataset semantik di `generated_kg/`. |
| **Kevin Antonio Wiyono Lauw** | 24/535917/PA/22736 | QA & DevOps Engineer | Membangun modul evaluasi kualitas otomatis (`evaluate_quality.py`). Merancang pipeline pengujian 3-tahap. Mengonfigurasi lingkungan Docker (`Dockerfile`, `docker-compose.yml`, `entrypoint.sh`). Menyusun laporan evaluasi dan analisis bug. |
| **Melinda Annastasia Budijono** | 24/542840/PA/23052 | Backend & Reverse Engineer | Mengembangkan logika pemetaan pola orkestrasi LangGraph pada `src/langgraph/`. Merancang template kode orkestrasi dinamis LangGraph. Mengembangkan modul reverse engineering (`Script/`). Menyusun dokumentasi repositori (`REPOSITORY_GUIDE.md`). |
