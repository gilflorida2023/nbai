# Article3

Article3 is a Python tool for summarizing articles from URLs using the Ollama API and benchmarking multiple models on multiple URLs. It supports caching to avoid redundant processing, JavaScript/cookie restriction detection, and structured summary output. The project includes two scripts:
- **`article3.py`**: Summarizes a single article from a URL using a specified Ollama model.
- **`article3_bench.py`**: Benchmarks up to 100 Ollama models on up to 50 URLs, outputting results to a CSV.

## Features
- Summarizes articles with a strict character limit (e.g., 257 characters) in `[Main Event] - [Key Detail] - [Outcome]` format.
- Caches article content and summaries in `~/.cache/article3`.
- Detects JavaScript/cookie restrictions and logs them to `~/.cache/article3/security_urls.txt`.
- Cleans prompt-related prefixes and brackets from summaries.
- Benchmarks models with metrics like response time, token counts, and success status.
- Outputs raw Ollama API errors (e.g., `400 Bad Request: {"error":"\"qwen3-embedding:0.6b\" does not support generate"}`).
- Supports `REPEATED` (regenerate summaries) and `CACHED` (reuse cached summaries) modes.

## Dependencies
### Python Dependencies
- Python 3.11.2
- `requests==2.32.3`
- `beautifulsoup4==4.12.3`
- `numpy==1.26.4` (for `article3_bench.py`)

### System Dependencies
- `jq`
- `lynx`
- `which`

## Installation
Clone the repository and install using one of the following methods: `venv`, `pipx`, or `setup.py`.

### Clone the Repository
	git clone https://github.com/gilflorida2023/article3.git
	cd article3


### Option 1: Install with venvCreate and activate a virtual environment:bash
	python3 -m venv venv
	source venv/bin/activate

### Install Python dependencies:bash
	pip install -r requirements.txt

### Ensure requirements.txt contains:
```
requests==2.32.3
beautifulsoup4==4.12.3
numpy==1.26.4
```

### Install system dependencies:bash
	sudo apt update
	sudo apt install jq lynx which

### Option 2: Install with pipxpipx installs the project in an isolated environment and makes article3 and article3_bench commands globally available.Install pipx:bash
	sudo apt update
	sudo apt install pipx
	pipx ensurepath

### Restart your terminal or run source ~/.bashrc to update your PATH.
### Install the project:bash
	cd article3
	pipx install .

### Alternatively, install directly from GitHub:bash
	pipx install git+https://github.com/gilflorida2023/article3.git

### Install system dependencies:bash
	sudo apt update
	sudo apt install jq lynx which

### Option 3: Install with setup.pyIf you prefer using setuptools directly (assumes pyproject.toml is configured):Create and activate a virtual environment:bash
	python3 -m venv venv
	source venv/bin/activate

### Install the project:bash
	cd article3
	pip install .

### Install system dependencies:bash
	sudo apt update
	sudo apt install jq lynx which

### Usage Using article3.py 
```
Summarizes a single article from a URL using an Ollama model.Syntax:bash
 article3 <OLLAMA_HOST> <URL> [OLLAMA_MODEL] [SUMMARY_LENGTH] [REPEATED|CACHED]

<OLLAMA_HOST>: Ollama server (e.g., 192.168.0.8:11434)
<URL>: Article URL
[OLLAMA_MODEL]: Optional model (default: llama3:8b)
[SUMMARY_LENGTH]: Optional summary length (default: 257)
[REPEATED|CACHED]: Optional mode (default: REPEATED)
```

### Examples:With venv:bash
```
source venv/bin/activate
python article3.py 192.168.0.8:11434 "https://www.thedailybeast.com/trump-lawyer-alan-dershowitz-admits-how-many-millions-he-earned-representing-epstein/" qwen3-embedding:0.6b 257 REPEATED
deactivate
```
### Output: Error: 400 Bad Request: {"error":"\"qwen3-embedding:0.6b\" does not support generate"}
### With pipx:bash

### article3 192.168.0.8:11434 "https://www.thedailybeast.com/trump-lawyer-alan-dershowitz-admits-how-many-millions-he-earned-representing-epstein/" llama3.2:3b 257 REPEATED

### Output: Dershowitz earned millions defending Epstein - Legal fees revealed in court - No impact on Trump campaign.

### Using article3_bench.py
### Benchmarks multiple Ollama models on multiple URLs, outputting results to article3_bench.csv.Syntax:bash
```
article3_bench <OLLAMA_HOST> <SUMMARY_LENGTH> [-m MODELS | -mf MODEL_FILE] [-u URLS | -uf URLS_FILE]

<OLLAMA_HOST>: Ollama server (e.g., 192.168.0.8:11434)
<SUMMARY_LENGTH>: Summary length (e.g., 257)
-m, --models: Comma-separated models (e.g., llama3:8b,qwen2.5:7b)
-mf, --model_file: File with models (one per line, # for comments)
-u, --urls: Comma-separated URLs
-uf, --urls_file: File with URLs (one per line, # for comments)
```
## Example Files:
### urls.txt:plaintext
```
https://www.theguardian.com/us-news/2025/sep/25/trump-cdc-budget-cuts-chronic-illness
https://www.thedailybeast.com/trump-lawyer-alan-dershowitz-admits-how-many-millions-he-earned-representing-epstein/
https://www.aljazeera.com/video/newsfeed/2025/9/26/aftermath-of-israeli-strikes-on-yemens-capital?traffic_source=rss
```

### models.txt:plaintext
```
llama3.2:3b
qwen2.5:3b
qwen3-embedding:0.6b
```
### Examples:With venv:bash
```
source venv/bin/activate
python article3_bench.py 192.168.0.8:11434 257 -uf urls.txt -mf models.txt
deactivate
```
### With pipx:bash
```
article3_bench 192.168.0.8:11434 257 -uf urls.txt -mf models.txt
```
### Output: CSV at article3_bench.csv with columns URL, Model, Time (s), Std Dev Time (s), Length (chars), Input Tokens, Output Tokens, Success, Error, Summary, Cache File, Summary Cache File.

### Example CSV Output
csv
```
"URL","Model","Time (s)","Std Dev Time (s)","Length (chars)","Input Tokens","Output Tokens","Success","Error","Summary","Cache File","Summary Cache File"
"https://www.thedailybeast.com/...","qwen3-embedding:0.6b","0.24","11.48","0","0","0","False","400 Bad Request: {\"error\":\"\\\"qwen3-embedding:0.6b\\\" does not support generate\"}","","/home/scout/.cache/article3/xxx.txt","/home/scout/.cache/article3/yyy_summary.txt"
"https://www.thedailybeast.com/...","llama3.2:3b","45.12","11.48","257","2800","64","True","","Dershowitz earned millions defending Epstein - Legal fees revealed in court - No impact on Trump campaign.","/home/scout/.cache/article3/xxx.txt","/home/scout/.cache/article3/zzz_summary.txt"
```
### NotesCaching: article3.py reuses cached summaries in CACHED mode; article3_bench.py uses REPEATED mode, always regenerating summaries.





## Files
### redundant
| Original<br>Filename | New<br>Filename | Purpose |
| :--- | :--- | :--------------------------: |
| tableintegrate.py | nbai.py | Summarize News boat articles |
| article3.sh | article_processor.py | Summarize url with AI |
| tabletpost.py | Blank | Format actions table for twitter |

### Parallel new versus old code. 
| Tool<br>Chains | Purpose | modified? |
| :------ | :--------------------------: | :--------------: |
| tableintegrate.py -> article3.sh | Original working code | Unmodified |
| nbai.py ->  article_processor.py | New | Modified |
