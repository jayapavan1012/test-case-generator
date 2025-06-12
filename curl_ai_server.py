#!/usr/bin/env python3
"""
AI-Powered CURL Command Generator Server

This server uses a powerful AI model (Deepseek-Coder-V2) via Ollama
to generate contextual curl commands for a given Spring Boot controller,
its DTOs, and user-defined scenarios.
"""

import argparse
import json
import logging
import requests
import sys
import signal
from flask import Flask, request, jsonify

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
OLLAMA_API_URL = ""
DEEPSEEK_MODEL_NAME = ""

# --- Ollama AI Interaction ---

def check_ollama_model_availability(ollama_base_url, model_name):
    """Checks if the required model is available on the Ollama server."""
    try:
        response = requests.get(f"{ollama_base_url}/api/tags")
        response.raise_for_status()
        models = response.json().get('models', [])
        for model in models:
            if model_name in model['name']:
                logger.info(f"✅ Found required model on Ollama: {model['name']}")
                return True
        logger.warning(f"⚠️ Ollama is running, but model '{model_name}' was not found.")
        logger.warning("Please ensure you have run `ollama pull {model_name}`.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Could not connect to Ollama at {ollama_base_url}. Error: {e}")
        return False

def generate_with_ai(prompt, max_tokens=8192):
    """Generates content using the Deepseek model via Ollama."""
    global OLLAMA_API_URL, DEEPSEEK_MODEL_NAME

    payload = {
        "model": DEEPSEEK_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.05,
            "top_p": 0.9,
            "num_ctx": 16384,
            "num_predict": max_tokens
        }
    }
    
    try:
        logger.info(f"Sending prompt to AI model '{DEEPSEEK_MODEL_NAME}'...")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        response_data = response.json()
        generated_text = response_data.get('response', '')
        
        # Clean the response to get just the script
        # The model sometimes wraps the output in markdown fences
        if "```bash" in generated_text:
            generated_text = generated_text.split("```bash")[1].split("```")[0]
        elif "```sh" in generated_text:
            generated_text = generated_text.split("```sh")[1].split("```")[0]
            
        return generated_text.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred with the Ollama request: {e}")
        raise RuntimeError(f"Ollama request failed: {e}")


def create_ai_prompt(controller_code, dto_codes, scenarios, base_url):
    """Creates the detailed prompt for the AI to generate curl commands."""
    
    dto_section = ""
    if dto_codes:
        for dto_name, dto_code in dto_codes.items():
            dto_section += f"### DTO: {dto_name}\n```java\n{dto_code}\n```\n\n"

    scenario_instructions = ""
    if scenarios:
        scenario_instructions = f"""
### Testing Scenarios to Cover
```text
{scenarios}
```
- Generate a `curl` command for EACH scenario described above.
"""
    else:
        scenario_instructions = """
### Task: Auto-Generate Test Scenarios
Since no specific scenarios were provided, you must analyze the controller and DTOs to create your own test cases. For each endpoint, you MUST generate `curl` commands for:
1.  **Success Case**: A request with valid data that should succeed (HTTP 200 or 201).
2.  **Failure Case**: A request with invalid, incomplete, or junk data that should fail (HTTP 400).
3.  **Edge Case (Optional but Recommended)**: A test for null values, empty strings, or other edge conditions where applicable.
"""

    prompt = f"""
You are an expert in testing Spring Boot applications. Your task is to generate a comprehensive, executable bash script of `curl` commands to test the endpoints in a given Java controller file.

### Target Base URL
{base_url}

### Controller Code
```java
{controller_code}
```

{dto_section}

{scenario_instructions}

### STRICT SCRIPTING REQUIREMENTS
1.  **Generate a Robust Bash Script**: Your output MUST be a valid, executable bash script (`#!/bin/bash`).
2.  **Readable Test Blocks**: For each test, create a block with clear visual separators (`echo "================="`).
3.  **Capture Response**: Use `RESPONSE=$(curl ...)` to capture the output. Use `-s` for silent mode and `-w "\\nHTTP_STATUS:%{{http_code}}"` to append the HTTP status.
4.  **Parse and Display Output**:
    -   Extract the HTTP status and body from the `RESPONSE` variable.
    -   Print the status and body with clear labels like `--> STATUS:` and `--> RESPONSE BODY:`.
5.  **Conditional `jq` Formatting**:
    -   Before using `jq`, check if it's installed with `if command -v jq >/dev/null; then`.
    -   If it is, pipe the response body to `jq .`.
    -   If not, just `echo` the raw response body with a note. This makes `jq` optional and prevents errors.
6.  **Completeness**: The script should be complete and ready to run. Include a note at the top that `jq` is recommended for the best experience.


**Example of a single test block in the script:**
```bash
echo "=============================================="
echo "--- Testing: Create User - SUCCESS ---"
echo "=============================================="

# Capture the full response (body and status code)
RESPONSE=$(curl -s -w "\\nHTTP_STATUS:%{{http_code}}" -X POST 'http://localhost:8080/api/users' \\
-H "Content-Type: application/json" \\
-H "Accept: application/json" \\
--data-raw '{{
    "name": "John Doe",
    "email": "john.doe@example.com"
}}')

# Extract status and body
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

# Print the results
echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"

# Check if jq is installed and use it to format the JSON if it is
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""
```

Generate the complete bash script now.
"""
    return prompt


# --- Flask API Endpoint ---

@app.route('/generate-curls', methods=['POST'])
def handle_generate_curls():
    """
    Handles the request to generate curl commands.
    Expects JSON: {
        "controller_code": "...",
        "dto_codes": { "UserDto.java": "..." },
        "scenarios": "...",
        "base_url": "http://localhost:8080"
    }
    """
    logger.info("Received request for /generate-curls")
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    controller_code = data.get("controller_code")
    dto_codes = data.get("dto_codes", {})
    scenarios = data.get("scenarios")
    base_url = data.get("base_url", "http://localhost:8080")

    if not all([controller_code, scenarios is not None]):
        return jsonify({"error": "Missing required fields: 'controller_code' and 'scenarios' are required (scenarios can be an empty string)."}), 400

    try:
        # 1. Create the prompt for the AI
        prompt = create_ai_prompt(controller_code, dto_codes, scenarios, base_url)
        
        # 2. Generate the script using the AI
        generated_script = generate_with_ai(prompt)
        
        # 3. Return the generated script
        return jsonify({
            "status": "success",
            "script_content": generated_script
        })

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

def main():
    """Main function to run the server."""
    global OLLAMA_API_URL, DEEPSEEK_MODEL_NAME
    
    parser = argparse.ArgumentParser(description="AI cURL Generator Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=9093, help="Port for this server (different from test generator).")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="URL of the Ollama server.")
    parser.add_argument("--model", type=str, default="deepseek-coder-v2:16b", help="Name of the Deepseek model to use.")
    args = parser.parse_args()
    
    OLLAMA_API_URL = f"{args.ollama_url}/api/generate"
    DEEPSEEK_MODEL_NAME = args.model
    
    # Check for Ollama and model availability at startup
    if not check_ollama_model_availability(args.ollama_url, args.model):
        logger.error("Shutting down due to model unavailability.")
        sys.exit(1)
        
    def signal_handler(sig, frame):
        logger.info('Shutting down server...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"🚀 Starting AI cURL Generator Server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main() 