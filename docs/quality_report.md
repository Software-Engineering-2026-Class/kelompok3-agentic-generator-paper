# Laporan Evaluasi Kualitas Kode LangGraph (Issue #07)

> Evaluasi dilakukan **offline** tanpa kuota OpenAI menggunakan:
> `py_compile` (syntax) · `ast` (struktur) · `MockChatOpenAI` (runtime)

**Total skenario:** 9  |  **Rata-rata quality score:** 93.3/100

---

## Ringkasan Hasil per Skenario

| Skenario | Syntax | Tools IR→Kode | Agent Nodes | Prompt Bersih | Pattern | Runtime | **Score** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `chat-agent` | OK | 0/0 (OK) | 1/1 (OK) | IRI (1) | OK | OK | **80.0/100** |
| `email-agent` | OK | 1/1 (WARN) | 1/1 (OK) | OK | OK | OK | **100.0/100** |
| `open-code` | OK | 2/2 (WARN) | 1/1 (OK) | OK | OK | OK | **100.0/100** |
| `pizza-orderer` | OK | 2/2 (WARN) | 1/1 (OK) | IRI (1) | OK | OK | **80.0/100** |
| `stockbroker` | OK | 3/3 (WARN) | 1/1 (OK) | IRI (1) | OK | OK | **80.0/100** |
| `supervisor` | OK | 7/7 (WARN) | 1/1 (OK) | OK | OK | OK | **100.0/100** |
| `trip-planner` | OK | 4/4 (OK) | 1/1 (OK) | OK | OK | OK | **100.0/100** |
| `utils` | OK | 2/2 (OK) | 1/0 (OK) | OK | OK | OK | **100.0/100** |
| `writer-agent` | OK | 1/1 (OK) | 1/1 (OK) | OK | OK | OK | **100.0/100** |

---

## Detail Per-Skenario

### `chat-agent` — Score 80.0/100

- **Pattern KG:** `linear`
- **Syntax:** PASS
- **Tools di IR:** tidak ada
- **Tool functions di kode:** tidak ada
- **❌ IRI bocor ke prompt:** ['http://www.w3id.org/agentic-ai/onto#ChatSystemPrompt']
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `email-agent` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['unnamed__tool']
- **Tool functions di kode:** ['unnamed__tool']
- **⚠ Tool tanpa nama (unnamed):** 1 fungsi
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `open-code` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['unnamed__tool', 'unnamed__tool_1']
- **Tool functions di kode:** ['unnamed__tool', 'unnamed__tool_1']
- **⚠ Tool tanpa nama (unnamed):** 2 fungsi
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `pizza-orderer` — Score 80.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['unnamed__tool', 'unnamed__tool_1']
- **Tool functions di kode:** ['unnamed__tool', 'unnamed__tool_1']
- **⚠ Tool tanpa nama (unnamed):** 2 fungsi
- **❌ IRI bocor ke prompt:** ['http://www.w3id.org/agentic-ai/onto#prompt_agent_system']
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `stockbroker` — Score 80.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['unnamed__tool', 'unnamed__tool_1', 'unnamed__tool_2']
- **Tool functions di kode:** ['unnamed__tool', 'unnamed__tool_1', 'unnamed__tool_2']
- **⚠ Tool tanpa nama (unnamed):** 3 fungsi
- **❌ IRI bocor ke prompt:** ['http://www.w3id.org/agentic-ai/onto#StockbrokerSystemPrompt']
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `supervisor` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['unnamed__tool', 'unnamed__tool_1', 'unnamed__tool_2', 'unnamed__tool_3', 'unnamed__tool_4', 'unnamed__tool_5', 'unnamed__tool_6']
- **Tool functions di kode:** ['unnamed__tool', 'unnamed__tool_1', 'unnamed__tool_2', 'unnamed__tool_3', 'unnamed__tool_4', 'unnamed__tool_5', 'unnamed__tool_6']
- **⚠ Tool tanpa nama (unnamed):** 7 fungsi
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `trip-planner` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['extract', 'classify', 'list_accommodations', 'list_restaurants']
- **Tool functions di kode:** ['extract', 'classify', 'list_accommodations', 'list_restaurants']
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `utils` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['capitalize__utilities_capitalize_sentence_capitalize', 'format__messages__utility_format_messages']
- **Tool functions di kode:** ['capitalize__utilities_capitalize_sentence_capitalize', 'format__messages__utility_format_messages']
- **Pattern match:** Ya
- **Runtime (mock):** PASS

### `writer-agent` — Score 100.0/100

- **Pattern KG:** `tool_calling`
- **Syntax:** PASS
- **Tools di IR:** ['draft_text_document']
- **Tool functions di kode:** ['draft_text_document']
- **Pattern match:** Ya
- **Runtime (mock):** PASS
