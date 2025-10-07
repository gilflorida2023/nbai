# Article3

Article3 is a Python tool for summarizing articles from URLs using the Ollama API. It supports caching to avoid redundant processing, JavaScript/cookie restriction detection, and structured summary output. The project includes two scripts:
- **`article3.sh`**: Summarizes a single article from a URL using a specified Ollama model.

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

### System Dependencies
- `jq`
- `lynx`
- `which`

## Installation
Clone the repository and install using one of the following methods: `venv`, `pipx`, or `setup.py`.

### Clone the Repository
	git clone https://github.com/gilflorida2023/nbai.git
	cd nbai


### Option 1: Install with venv. Create and activate a virtual environment:bash
	python3 -m venv venv
	source venv/bin/activate

### Install Python dependencies:bash
	pip install -r requirements.txt

### Install system dependencies:bash
	sudo apt update
	sudo apt install jq lynx which

### Option 2: Install with pipx

### pipx installs the project in an isolated environment and makes commands globally available.
### Install pipx:
```bash
	sudo apt update
	sudo apt install pipx
	pipx ensurepath
```
### Restart your terminal or run source ~/.bashrc to update your PATH.
### Install the project:
	cd article3
	pipx install .

### Alternatively, install directly from GitHub:bash
	pipx install git+https://github.com/gilflorida2023/nbai.git

### Install system dependencies:
	sudo apt update
	sudo apt install jq lynx which

### Option 3: Install with setup.pyIf you prefer using setuptools directly (assumes pyproject.toml is configured):Create and activate a virtual environment:bash
	python3 -m venv venv
	source venv/bin/activate

### Install the project:
	cd nbai
	pip install .

### Install system dependencies:
	sudo apt update
	sudo apt install jq lynx which

### NotesCaching: article3.sh reuses cached summaries in CACHED mode;  REPEATED mode, always regenerates summaries.
### Usage Using article3.sh 
```
Summarizes a single article from a URL using an Ollama model.Syntax:bash
 article3.sh <OLLAMA_HOST> <URL> [OLLAMA_MODEL] [SUMMARY_LENGTH] [REPEATED|CACHED]

<OLLAMA_HOST>: Ollama server (e.g., 192.168.0.8:11434)
<URL>: Article URL
[OLLAMA_MODEL]: Optional model (default: llama3:8b)
[SUMMARY_LENGTH]: Optional summary length (default: 257)
[REPEATED|CACHED]: Optional mode (default: REPEATED)
```

### Examples:With venv:
```
source venv/bin/activate
python article3.sh 192.168.0.8:11434 "https://www.thedailybeast.com/trump-lawyer-alan-dershowitz-admits-how-many-millions-he-earned-representing-epstein/" qwen3-embedding:0.6b 257 REPEATED
deactivate
```

## Files
### redundant
| Original<br>Filename | New<br>Filename | Purpose |
| :--- | :--- | :-------------------------- |
| tableintegrate.py | nbai.py | Summarize News boat articles |
| article3.sh | article_processor.py | Summarize url with AI |
| tabletpost.py | Blank | Format actions table for twitter |

### Parallel new versus old code. 
| Tool<br>Chains | Purpose | modified? |
| :------ | :--------------------------: | :--------------: |
| tableintegrate.py -> article3.sh | Original working code | Unmodified |
| nbai.py ->  article_processor.py | New | Modified |



## This is how I currently use newsboat with scripts.sh and tableintegrate.sh:
```
while :
do
    newsboat 
    python3 -m venv venv 2> /dev/null
    
    source venv/bin/activate 
    pip install -r requirements.txt
    cd scripts
    python ./tableintegrate.py 192.168.0.10:11434
    python ./tabletpost.py 
    deactivate
    sleep 1
done
```
