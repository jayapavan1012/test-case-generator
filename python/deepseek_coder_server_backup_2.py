#!/usr/bin/env python3
"""
OPTIMIZED JUnit Test Generator using Deepseek-Coder-V2:16b
- Deepseek-Coder-V2:16b (Ollama) - PRIMARY MODEL
- Deepseek-Coder 6.7B-Instruct (Local llama-cpp) - FALLBACK
AWS g5.2xlarge (24GB A10G GPU + 32GB RAM + 8 vCPUs) - PRODUCTION READY
"""

import argparse
import json
import logging
import psutil
import time
import signal
import sys
import requests
from flask import Flask, request, jsonify

# Import with graceful fallback
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️  llama-cpp-python not available - Deepseek 6.7B fallback will use demo mode")

# Optimized logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DeepSeekV2Generator:
    """Production-ready Deepseek-Coder-V2:16b generator for AWS g5.2xlarge"""
    
    def __init__(self):
        # Primary Ollama Deepseek-V2 model
        self.ollama_base_url = "http://127.0.0.1:11434"
        self.ollama_model = "deepseek-coder-v2:16b"
        self.deepseek_v2_available = False
        
        # Fallback local Deepseek 6.7B model
        self.deepseek_6b_model = None
        self.deepseek_6b_loaded = False
        
        # Shared cache
        self.generation_cache = {}
        
        # OPTIMIZED settings for Deepseek-Coder-V2:16b
        self.max_tokens = 2048      # Adjusted for memory stability on large inputs
        self.temperature = 0.1      # Low for deterministic output
        self.top_p = 0.95          # High for stability
        self.repeat_penalty = 1.05  # Minimal to avoid issues
        
        self.prompt_template = """### Instruction:
You are an expert Java test engineer. Your task is to generate a complete, high-quality JUnit 5 test class for the provided Java source code.
Your response must be only the raw Java code for the test class, enclosed in a single '```java' block.
Do not add any comments, explanations, or introductory text outside the code block.

### Input Java Class:
{java_code}

### Response (JUnit 5 Test Class):
```java
"""

    def check_deepseek_v2_status(self):
        """Check if Ollama Deepseek-Coder-V2:16b is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    model_name = model.get('name', '').lower()
                    if 'deepseek-coder-v2' in model_name and '16b' in model_name:
                        self.deepseek_v2_available = True
                        logger.info(f"✅ Deepseek-Coder-V2:16b available: {model.get('name')}")
                        return True
                logger.warning("⚠️  Ollama running but Deepseek-Coder-V2:16b model not found")
                
                # Check for any deepseek-coder model as fallback
                for model in models:
                    if 'deepseek-coder' in model.get('name', '').lower():
                        logger.info(f"📦 Found alternative Deepseek model: {model.get('name')}")
                        self.ollama_model = model.get('name')
                        self.deepseek_v2_available = True
                        return True
                return False
            else:
                logger.warning(f"⚠️  Ollama responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Ollama not available: {str(e)}")
            self.deepseek_v2_available = False
            return False
    
    def generate_with_deepseek_v2(self, prompt, max_tokens=None):
        """Generate using Ollama Deepseek-Coder-V2:16b"""
        try:
            if not self.deepseek_v2_available:
                raise Exception("Deepseek-Coder-V2 not available")
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "repeat_penalty": self.repeat_penalty,
                    "num_predict": max_tokens or self.max_tokens,
                    "num_ctx": 4096  # Adjusted for stability with large prompts
                }
            }
            
            logger.info("--- Full Prompt Sent to Model ---")
            logger.info(prompt)
            logger.info("-----------------------------------")

            try:
                import json
                curl_url = f"{self.ollama_base_url}/api/generate"
                # Pretty-print the JSON for the here document, making it readable and safe
                json_payload_str = json.dumps(payload, indent=2)
                # Use a heredoc for robustness. The user can copy-paste the entire multi-line command.
                # The 'EOF' is quoted to prevent shell expansion within the JSON.
                curl_command = f"""curl -X POST '{curl_url}' -H "Content-Type: application/json" --data @- <<'EOF'
{json_payload_str}
EOF"""
                
                logger.info("")
                logger.info("")
                logger.info("--- Equivalent cURL Command for Debugging ---")
                logger.info("# (Run this in your terminal. It uses a 'here document' for safety.)")
                logger.info(curl_command)
                logger.info("---------------------------------------------")
                logger.info("")
                logger.info("")
            except Exception as e:
                logger.warning(f"⚠️  Could not generate cURL command for logging: {e}")

            logger.info("--- Sending POST request to Ollama server ---")
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate", 
                json=payload, 
                timeout=120  # Increased timeout for longer generation
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                # Prepare truncated text for safe logging
                truncated_text = response_text.replace('\n', ' ')[:400]
                logger.info(f"📝 Deepseek raw response (truncated): {truncated_text}...")
                return {
                    'choices': [{'text': response_text}]
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Deepseek-V2 generation failed: {str(e)}")
            raise e

    def initialize_deepseek_6b_model(self, model_path, use_gpu=True):
        """Initialize Deepseek 6.7B model with OPTIMAL settings for AWS g5.2xlarge"""
        try:
            if not LLAMA_CPP_AVAILABLE:
                logger.warning("Running in DEMO mode - llama-cpp-python not available")
                self.deepseek_6b_loaded = True
                return True
            
            # System info
            mem = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            logger.info(f"System: {mem.total/(1024**3):.1f}GB RAM, {cpu_count} CPU cores")
            logger.info(f"Available: {mem.available/(1024**3):.1f}GB RAM")
            
            # PROVEN stable settings for g5.2xlarge
            if use_gpu:
                config = {
                    "n_gpu_layers": -1,
                    "n_threads": 4,
                    "n_batch": 256,
                    "n_ctx": 2048, # Increased context
                    "use_mmap": True,
                    "use_mlock": False,
                    "low_vram": False,
                    "f16_kv": True,
                    "logits_all": False,
                }
                logger.info("🎮 GPU MODE: 24GB A10G optimized")
            else:
                config = {
                    "n_gpu_layers": 0,
                    "n_threads": 6,
                    "n_batch": 128,
                    "n_ctx": 2048,
                    "use_mmap": True,
                    "use_mlock": False,
                    "f16_kv": True,
                }
                logger.info("💻 CPU MODE: 8 vCPU + 32GB RAM")
            
            logger.info(f"Loading Deepseek-Coder 6.7B from: {model_path}")
            
            self.deepseek_6b_model = Llama(model_path=model_path, verbose=False, **config)
            
            mem_after = psutil.virtual_memory()
            memory_used = (mem.available - mem_after.available) / (1024**3)
            logger.info(f"✅ Deepseek model loaded successfully! Memory used: {memory_used:.2f}GB")
            
            self.deepseek_6b_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Deepseek model loading failed: {str(e)}")
            self.deepseek_6b_loaded = False
            return False

    def generate_junit_tests(self, java_code, class_name=None, model_type="auto"):
        """Generate JUnit tests with DEEPSEEK-V2 SUPPORT"""
        logger.info("--- Starting Test Generation Pipeline ---")
        logger.info(f"Model: {model_type}, Class: {class_name}, Code length: {len(java_code)}")

        # Auto-select best available model
        if model_type == "auto":
            if self.deepseek_v2_available:
                model_type = "deepseek-v2"
            elif self.deepseek_6b_loaded:
                model_type = "deepseek-6b"
            else:
                model_type = "demo"
            logger.info(f"🤖 Auto-selected model: {model_type}")

        cache_key = hash(java_code + str(class_name) + model_type)
        if cache_key in self.generation_cache:
            logger.info(f"📦 Returning cached result for key {cache_key}")
            return self.generation_cache[cache_key]
        
        logger.info("Cache miss. Proceeding with new generation.")
        if not class_name:
            class_name = self._extract_class_name(java_code)
        
        methods = self._extract_methods(java_code)
        method_list = "\n".join([f"- {m}" for m in methods]) if methods else "No public methods found to test."
        
        # New, robust prompt format for instruction-tuned models
        prompt = self.prompt_template.format(
            java_code=java_code
        )
        
        try:
            start_time = time.time()
            logger.info(f"🔄 Generating for {class_name} using {model_type.upper()} (prompt: {len(prompt)} chars)")
            
            if model_type == "deepseek-v2" and self.deepseek_v2_available:
                output = self.generate_with_deepseek_v2(prompt, self.max_tokens)
                model_name = "Deepseek-Coder-V2:16b"
            elif model_type == "deepseek-6b" and self.deepseek_6b_loaded and self.deepseek_6b_model:
                output = self.deepseek_6b_model(prompt, max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p, repeat_penalty=self.repeat_penalty, stop=["```", "}\n}"], echo=False)
                model_name = "Deepseek-Coder 6.7B"
            else:
                logger.warning(f"⚠️  Model '{model_type}' not available, using demo tests.")
                return self._generate_demo_tests(java_code, class_name), "Demo Mode"
            
            generation_time = time.time() - start_time
            
            if not output or 'choices' not in output or not output['choices'] or not output['choices'][0]['text'].strip():
                logger.warning("⚠️  Model returned an empty response. Falling back to demo tests.")
                return self._generate_demo_tests(java_code, class_name), "Demo Mode"
            
            logger.info(f"✅ Generation completed in {generation_time:.2f}s using {model_name}")
            
            generated_text = output['choices'][0]['text']
            cleaned_code = self._clean_generated_code(generated_text, class_name)
            
            if not self._validate_generated_code(cleaned_code, class_name):
                logger.warning("⚠️  Generated code failed validation. Falling back to demo tests.")
                return self._generate_demo_tests(java_code, class_name), "Demo Mode"
            
            logger.info("✅ Code validation successful.")
            result_tuple = (cleaned_code, model_name)
            self.generation_cache[cache_key] = result_tuple
            return result_tuple
            
        except Exception as e:
            logger.error(f"❌ Exception in generation pipeline: {type(e).__name__}: {str(e)}")
            return self._generate_demo_tests(java_code, class_name), "Demo Mode"

    def _validate_generated_code(self, code, class_name):
        """Validate the generated test code with detailed logging."""
        logger.info("--- Starting Code Validation ---")
        try:
            if not code or not isinstance(code, str) or len(code.strip()) < 50:
                logger.info("Validation failed: code is empty, not a string, or too short.")
                return False
            if "import org.junit.jupiter.api" not in code:
                logger.info("Validation failed: missing JUnit imports.")
                return False
            if f"class {class_name}Test" not in code:
                logger.info(f"Validation failed: incorrect test class name. Expected '{class_name}Test'")
                return False
            if "@Test" not in code:
                logger.info("Validation failed: no @Test annotation found.")
                return False
            # @BeforeEach is good practice but not strictly required
            # if "@BeforeEach" not in code:
            #     logger.info("Validation failed: no @BeforeEach method.")
            #     return False
            logger.info("--- Code Validation Passed ---")
            return True
        except Exception as e:
            logger.error(f"❌ Exception during code validation: {str(e)}")
            return False

    def _generate_demo_tests(self, java_code, class_name):
        """High-quality demo tests when model fails"""
        logger.info(f"--- Generating Demo Fallback Tests for {class_name} ---")
        if not class_name:
            class_name = self._extract_class_name(java_code)
        
        methods = self._extract_methods(java_code)
        
        test_methods = []
        for method in methods[:3]:
            clean_method = method.replace("()", "").strip()
            test_methods.append(f"""
    @Test
    @DisplayName("Test {clean_method}")
    void test{clean_method.title()}() {{
        // TODO: Implement test for {method}
        assertNotNull(testInstance);
    }}""")
        
        demo_code = f"""import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("{class_name} Test Suite (DEMO)")
public class {class_name}Test {{
    
    private {class_name} testInstance;
    
    @BeforeEach
    void setUp() {{
        // TODO: Initialize testInstance with mocked dependencies if needed
        testInstance = new {class_name}();
    }}
{''.join(test_methods)}
    
    @Test
    @DisplayName("Test object initialization")
    void testInitialization() {{
        assertNotNull(testInstance);
    }}
}}"""
        return demo_code

    def _extract_class_name(self, java_code):
        """Extract class name from Java code"""
        logger.info("--- Starting Class Name Extraction ---")
        try:
            match = re.search(r'public\s+(?:final\s+)?class\s+(\w+)', java_code)
            if match:
                class_name = match.group(1)
                logger.info(f"✅ Found class name via regex: {class_name}")
                return class_name
        except Exception as e:
             logger.error(f"❌ Exception in _extract_class_name regex: {e}")
        
        logger.warning("Regex failed, falling back to line-by-line search.")
        for line in java_code.split('\n'):
            line = line.strip()
            if 'class ' in line and 'public ' in line:
                parts = line.split('class ')
                if len(parts) > 1:
                    name = parts[1].split(' ')[0].split('{')[0].strip()
                    if name:
                        logger.info(f"✅ Found class name via fallback: {name}")
                        return name
        
        logger.error("❌ Could not find class name, falling back to 'TestClass'")
        return "TestClass"

    def _extract_methods(self, java_code):
        """Extract method signatures from Java code using a robust regex that handles annotations."""
        logger.info("--- Starting Method Extraction ---")
        methods = []
        try:
            import re
            # Regex to find public methods, ignoring annotations and handling multi-line params.
            pattern = re.compile(
                r'public\s+(?:static\s+)?'  # Modifier
                r'[\w\<\>\[\]\.,\s]+?\s+'  # Non-greedy return type
                r'(\w+)\s*'  # Method Name (the only capture group)
                r'\([\s\S]*?\)\s*'  # Parameters (multi-line)
                r'(?:throws\s+[\w\.,\s]+)?\s*{'
            )
            matches = pattern.findall(java_code)
            logger.info(f"Found {len(matches)} potential public methods using regex.")
            
            for method_name in matches:
                if method_name not in ['class', 'interface', 'enum']:
                    logger.info(f"  -> Extracted method: {method_name}()")
                    methods.append(f"{method_name}()")

            if not methods:
                 logger.warning("⚠️  Could not extract any public methods. The model will receive an empty method list.")
            else:
                logger.info(f"✅ Successfully extracted methods: {methods}")
        except Exception as e:
            logger.error(f"❌ Exception during method extraction: {str(e)}")
        
        logger.info("--- Finished Method Extraction ---")
        return methods[:5]  # Max 5 methods

    def _clean_generated_code(self, generated_text, class_name):
        """Clean and format generated code by extracting the final Java code block."""
        logger.info("--- Starting Code Cleaning ---")
        log_text = generated_text.replace('\n', ' ')[:300]
        logger.info(f"Raw generated text (first 300 chars): {log_text}")
        try:
            # Find the last occurrence of a Java code block.
            # This is more robust if the model adds introductory text with examples.
            last_code_block_start = generated_text.rfind("```java")
            if last_code_block_start != -1:
                # Find the end of that block
                end_block = generated_text.find("```", last_code_block_start + 7)
                if end_block != -1:
                    code = generated_text[last_code_block_start + 7 : end_block]
                    logger.info("✅ Extracted final Java code block from response.")
                    return code.strip()

            logger.warning("⚠️  Could not find a '```java ... ```' block. Falling back to other methods.")
            
            # Fallback for when the model doesn't use markdown fences
            import_pos = generated_text.find("import ")
            if import_pos != -1:
                logger.info("✅ Found 'import' statement, trimming preceding text.")
                return generated_text[import_pos:].strip()

            logger.warning("⚠️  No Java code block or 'import' statement found. Returning raw text for validation.")
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"❌ Exception in _clean_generated_code: {e}")
            return generated_text # Return original text on error

    def get_system_info(self):
        """Get current system status"""
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "total_memory_gb": round(mem.total / (1024**3), 2),
            "available_memory_gb": round(mem.available / (1024**3), 2),
            "memory_percent": round(mem.percent, 1),
            "cpu_percent": round(cpu_percent, 1),
            "model_loaded": self.deepseek_6b_loaded,
            "cache_size": len(self.generation_cache)
        }

# Global generator instance
generator = DeepSeekV2Generator()

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check with multi-model system info"""
    # Check Ollama status on health check
    generator.check_deepseek_v2_status()
    
    return jsonify({
        "status": "healthy",
        "server": "AWS g5.2xlarge (24GB A10G + 32GB RAM + 8 vCPUs)",
        "models": {
            "deepseek-6b": {
                "name": "Deepseek-Coder 6.7B-Instruct Q4_K_M",
                "status": "loaded" if generator.deepseek_6b_loaded else "not_loaded",
                "type": "local_llama_cpp"
            },
            "deepseek-v2": {
                "name": "Deepseek-Coder-V2:16b",
                "status": "available" if generator.deepseek_v2_available else "not_available",
                "type": "ollama_api",
                "url": generator.ollama_base_url
            }
        },
        "version": "Multi-Model Production v1.2-debug",
        "system": generator.get_system_info(),
    }), 200

@app.route('/models/status', methods=['GET'])
def models_status():
    """Get detailed status of all available models"""
    generator.check_deepseek_v2_status()
    
    return jsonify({
        "deepseek-6b": { "loaded": generator.deepseek_6b_loaded },
        "deepseek-v2": { "available": generator.deepseek_v2_available, "model": generator.ollama_model },
        "auto_selection_order": ["deepseek-v2", "deepseek-6b", "demo"]
    }), 200

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize Deepseek model (Ollama is external)"""
    try:
        data = request.get_json() or {}
        model_path = data.get('model_path', '/home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf')
        use_gpu = data.get('use_gpu', True)
        
        logger.info(f"🚀 Initializing Deepseek model: GPU={use_gpu}")
        success = generator.initialize_deepseek_6b_model(model_path, use_gpu)
        
        generator.check_deepseek_v2_status()
        
        if success:
            return jsonify({ "status": "success", "message": "Deepseek-Coder 6.7B initialized" }), 200
        else:
            return jsonify({ "status": "error", "message": "Failed to initialize Deepseek model" }), 500
            
    except Exception as e:
        logger.error(f"❌ Initialization error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate JUnit tests - MULTI-MODEL SUPPORT"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        java_code = data.get('prompt', '').strip()
        class_name = data.get('className')
        model_type = data.get('model', 'auto')
        
        if not java_code:
            return jsonify({"error": "No Java code provided"}), 400
        
        valid_models = ['auto', 'deepseek-v2', 'deepseek-6b', 'demo']
        if model_type not in valid_models:
            return jsonify({"error": f"Invalid model type. Valid options: {valid_models}"}), 400
        
        if model_type in ['auto', 'deepseek-v2']:
            generator.check_deepseek_v2_status()
        
        start_time = time.time()
        
        generated_tests, model_name = generator.generate_junit_tests(java_code, class_name, model_type)
        
        generation_time = time.time() - start_time
        
        return jsonify({
            "response": generated_tests,
            "generation_time_seconds": round(generation_time, 2),
            "server": "AWS g5.2xlarge",
            "model_used": model_name,
            "model_requested": model_type,
            "input_length": len(java_code),
            "system": generator.get_system_info()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Top-level generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear generation cache"""
    cache_size = len(generator.generation_cache)
    generator.generation_cache.clear()
    logger.info(f"Cache cleared. Removed {cache_size} items.")
    return jsonify({ "status": "success", "message": f"Cleared {cache_size} cached items" }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-Model JUnit Test Generator')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--model-path', default='/home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf')
    parser.add_argument('--use-gpu', action='store_true', default=True, help='Enable GPU for Deepseek')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🚀 DEEPSEEK-CODER-V2 JUnit Test Generator - AWS g5.2xlarge")
    logger.info(f"🌐 Server starting on {args.host}:{args.port}")
    logger.info("=" * 70)
    
    generator.check_deepseek_v2_status()
    
    def signal_handler(sig, frame):
        logger.info("🛑 Shutting down server gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app.run(host=args.host, port=args.port, debug=False) 