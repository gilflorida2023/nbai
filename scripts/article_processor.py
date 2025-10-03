#!/usr/bin/env python3
"""
article_processor.py: Process a URL using an Ollama host for summarization.

Usage:
    python article_processor.py <ollama_host> <url> [ollama_model] [summary_length] [repeated]
"""

import sys
import os
import hashlib
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json

def clean_text(text):
    """
    Clean text by removing thinking tags and normalizing.
    
    Args:
        text (str): Text to clean
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    # Remove thinking tags and patterns
    text = re.sub(r'<\s*[Tt][Hh][Ii][Nn][Kk]\s*>.*?</\s*[Tt][Hh][Ii][Nn][Kk]\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'[Tt][Hh][Ii][Nn][Kk][\.\s]*\.+\s*done thinking\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^[ \t]*[Tt][Hh][Ii][Nn][Kk][Ii][Nn][Gg][ \t]*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'^[ \t]+|[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def validate_ollama_host(host, context):
    """
    Validate that the Ollama host is provided.
    
    Args:
        host (str): Ollama host address
        context (str): Context for error message
    """
    if not host:
        print(f"Error: OLLAMA_HOST must be provided ({context})", file=sys.stderr)
        print(f"Usage: article_processor.py <ollama_host> <url> [ollama_model] [summary_length] [repeated]", file=sys.stderr)
        sys.exit(1)

def check_ollama_server(host):
    """
    Verify Ollama server is accessible.
    
    Args:
        host (str): Ollama host address
    """
    validate_ollama_host(host, "check_ollama_server")
    print("Checking Ollama server status...", file=sys.stderr)
    try:
        response = requests.get(f"http://{host}/api/tags", timeout=5)
        response.raise_for_status()
        print("Ollama server connection successful", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error: Cannot connect to Ollama at {host}: {str(e)}", file=sys.stderr)
        print("Verify the server is running and accessible", file=sys.stderr)
        sys.exit(1)

def check_model_available(host, model):
    """
    Verify the specified model is available on the Ollama server.
    
    Args:
        host (str): Ollama host address
        model (str): Model name
    """
    validate_ollama_host(host, "check_model_available")
    print(f"Checking if model '{model}' is available...", file=sys.stderr)
    try:
        response = requests.get(f"http://{host}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        if not any(m["name"] == model for m in models):
            print(f"Error: Model '{model}' not found on server", file=sys.stderr)
            print("Available models:", file=sys.stderr)
            for m in models:
                print(f"  {m['name']}", file=sys.stderr)
            sys.exit(1)
        print(f"Model '{model}' is available", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error checking model availability: {str(e)}", file=sys.stderr)
        sys.exit(1)

def unload_ollama_models(host):
    """
    Unload all models from the Ollama server.
    
    Args:
        host (str): Ollama host address
    """
    validate_ollama_host(host, "unload_ollama_models")
    print("Checking loaded models...", file=sys.stderr)
    try:
        response = requests.get(f"http://{host}/api/ps", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        if not models:
            print("No models currently loaded.", file=sys.stderr)
            return

        print("Found loaded models:", file=sys.stderr)
        for model in models:
            print(f"  {model['name']}", file=sys.stderr)

        unload_errors = 0
        for model in models:
            model_name = model["name"]
            print(f"Unloading {model_name}... ", end="", file=sys.stderr)
            try:
                requests.post(
                    f"http://{host}/api/generate",
                    json={"model": model_name, "prompt": "", "keep_alive": 0},
                    timeout=5
                ).raise_for_status()
                # Verify unload
                response = requests.get(f"http://{host}/api/ps", timeout=5)
                response.raise_for_status()
                if any(m["name"] == model_name for m in response.json().get("models", [])):
                    print("❌", file=sys.stderr)
                    unload_errors += 1
                else:
                    print("✅", file=sys.stderr)
            except requests.RequestException:
                print("❌", file=sys.stderr)
                unload_errors += 1

        if unload_errors > 0:
            print(f"article3 Warning: Failed to unload {unload_errors} model(s)", file=sys.stderr)
        else:
            print("article3 All models unloaded successfully", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error unloading models: {str(e)}", file=sys.stderr)

def get_cache_file(url):
    """
    Generate cache file path based on URL hash.
    
    Args:
        url (str): URL to hash
    Returns:
        Path: Cache file path
    """
    cache_dir = Path.home() / ".cache" / "article3"
    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{url_hash}.txt"
    print(f"Cache file: {cache_file}", file=sys.stderr)
    return cache_file

def check_repeated_content(cache_file, allow_repeated):
    """
    Check if cached content is fresh and should be reused.
    
    Args:
        cache_file (Path): Path to cache file
        allow_repeated (str): Whether to allow repeated content ("REPEATED" or not)
    Returns:
        str or None: "REPEATED" if content should be reused, None otherwise
    """
    if allow_repeated == "REPEATED":
        print("Skipping repeat check (REPEATED flag set)", file=sys.stderr)
        return None
    if cache_file.exists():
        current_time = time.time()
        file_mtime = cache_file.stat().st_mtime
        cache_age_hours = (current_time - file_mtime) / 3600
        print(f"Cache file age: {cache_age_hours:.1f}h", file=sys.stderr)
        if cache_age_hours < 24:
            return "REPEATED"
    return None

def fetch_article_content(url, cache_file):
    """
    Fetch article content and cache it, or use cached content if fresh.
    
    Args:
        url (str): URL to fetch
        cache_file (Path): Path to cache file
    Returns:
        str: Article content
    """
    if cache_file.exists():
        current_time = time.time()
        file_mtime = cache_file.stat().st_mtime
        cache_age_hours = (current_time - file_mtime) / 3600
        print(f"Cache file age: {cache_age_hours:.1f}h", file=sys.stderr)
        if cache_age_hours < 24:
            print("Using cached content", file=sys.stderr)
            return cache_file.read_text()
        else:
            print("Refreshing expired cache...", file=sys.stderr)
    print("Fetching new content...", file=sys.stderr)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        # Convert HTML to text using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        # Mimic lynx -dump -nolist -width=80
        text = re.sub(r'\s+', ' ', text).strip()
        cache_file.write_text(text)
        return text
    except requests.RequestException as e:
        print(f"Error fetching content: {str(e)}", file=sys.stderr)
        sys.exit(1)

def generate_summary(host, model, prompt, content):
    """
    Generate a summary using the Ollama API.
    
    Args:
        host (str): Ollama host address
        model (str): Model name
        prompt (str): Prompt for summarization
        content (str): Article content
    Returns:
        str: Generated summary
    """
    validate_ollama_host(host, "generate_summary")
    full_prompt = f"{prompt}\n\n{content}"
    print("Generating summary (this may take a moment)...", file=sys.stderr)
    try:
        print("Sending API request...", file=sys.stderr)
        response = requests.post(
            f"http://{host}/api/generate",
            json={"model": model, "prompt": full_prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        result = response.json().get("response")
        if not result:
            print("Invalid API response format", file=sys.stderr)
            sys.exit(1)
        return clean_text(result)
    except requests.RequestException as e:
        print(f"API request failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: article_processor.py <ollama_host> <url> [ollama_model] [summary_length] [repeated]", file=sys.stderr)
        sys.exit(1)

    ollama_host = sys.argv[1]
    url = sys.argv[2]
    ollama_model = sys.argv[3] if len(sys.argv) > 3 else "qwen3:1.7b"
    summary_length = int(sys.argv[4]) if len(sys.argv) > 4 else 257
    allow_repeated = sys.argv[5] if len(sys.argv) > 5 else "no"

    # Debug output
    print(f"Using host: {ollama_host}", file=sys.stderr)
    print(f"Using model: {ollama_model}", file=sys.stderr)
    print(f"Summary length: {summary_length}", file=sys.stderr)
    print(f"Allow repeated content: {allow_repeated}", file=sys.stderr)

    # Validate Ollama server and model
    check_ollama_server(ollama_host)
    check_model_available(ollama_host, ollama_model)

    # Cache setup
    cache_file = get_cache_file(url)
    if repeated_result := check_repeated_content(cache_file, allow_repeated):
        print(repeated_result)
        sys.exit(0)

    # Unload models
    unload_ollama_models(ollama_host)

    # Fetch content
    content = fetch_article_content(url, cache_file)

    # Generate prompt
    summary_prompt = (
        f"Respond ONLY with the {summary_length}-character summary. No thinking output. Summary: "
        f"Provide a **strictly {summary_length}-character** summary of this article. "
        f"Structure: [Main Event] - [Key Detail] - [Outcome]. "
        f'Example: "Israel approves new Gaza offensive amid ceasefire talks; military plans phased operations while US seeks deal." '
        f"**Rules:** "
        f"1. **EXACTLY {summary_length} chars** (count precisely). "
        f"2. **No incomplete words** (truncate mid-sentence if needed). "
        f"3. **No sources, dates, or author names.** "
        f"4. **If over limit, rewrite shorter.**"
    )

    # Generate summary
    summary = generate_summary(ollama_host, ollama_model, summary_prompt, content)

    # Fallback if empty
    if not summary or not summary.strip():
        print("Warning: Empty summary received, using fallback content", file=sys.stderr)
        summary = "[Error: No summary generated]"

    # Validate length
    length = len(summary)
    print(f"Generated summary length: {length}/{summary_length}", file=sys.stderr)
    if length > summary_length:
        print(f"Warning: Summary exceeded {summary_length} characters ({length})", file=sys.stderr)

    # Output summary
    print(summary)

    # Unload models again
    unload_ollama_models(ollama_host)
    sys.exit(0 if not summary.startswith("[Error") else 1)

if __name__ == "__main__":
    main()
