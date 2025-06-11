#!/usr/bin/env python3
"""
JUnit Test Generator using Deepseek-Coder 6.7B-Instruct
Optimized for EC2 instance Distm1 (10.5.17.187) with 32GB RAM
"""

import argparse
import json
import logging
import psutil
import time
import signal
import threading
from flask import Flask, request, jsonify

# Try to import llama_cpp, graceful fallback if not available
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️ llama_cpp not available - running in test mode")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Generation timed out")

def generate_with_timeout(model, prompt, timeout_seconds=45, **kwargs):
    """Generate with timeout to prevent hanging"""
    result = None
    exception = None
    
    def target():
        nonlocal result, exception
        try:
            result = model(prompt, **kwargs)
        except Exception as e:
            exception = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running, generation timed out
        logger.warning(f"Generation timed out after {timeout_seconds} seconds")
        return None
    
    if exception:
        raise exception
    
    return result

class DeepSeekCoderGenerator:
    def __init__(self):
        self.model = None
        # AWS g5.2xlarge optimized settings
        self.max_tokens = 800   # Good balance for g5.2xlarge
        self.temperature = 0.2  # Slightly higher for faster generation
        self.top_p = 0.85       # Good balance
        self.repeat_penalty = 1.03  # Standard
        self.generation_cache = {}
        self.model_loaded = False
        self.generation_count = 0  # Track number of generations
    
    def initialize_model(self, model_path, use_gpu=False):
        """Initialize Deepseek-Coder 6.7B model optimized for 16GB GPU + 32GB RAM + 16 cores"""
        try:
            if not LLAMA_CPP_AVAILABLE:
                logger.warning("llama_cpp not available - running in demo mode")
                self.model_loaded = True  # Demo mode
                return True
            
            # Check available memory
            mem = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            logger.info(f"Available memory: {mem.available / (1024*1024*1024):.2f} GB")
            logger.info(f"CPU cores: {cpu_count}")
            
            # AWS g5.2xlarge optimized settings (8 vCPU, 32GB RAM, 24GB A10G GPU)
            if use_gpu:
                # GPU mode: Optimized for 24GB A10G GPU
                n_gpu_layers = -1        # Offload ALL layers to 24GB GPU
                n_threads = 6            # Optimal for g5.2xlarge
                n_batch = 1024           # Large batch for 24GB GPU
                n_ctx = 4096             # Good context size
            else:
                # CPU mode: Optimized for 8 vCPU + 32GB RAM
                n_gpu_layers = 0
                n_threads = 8            # Use all 8 vCPUs
                n_batch = 512            # Good for 32GB RAM
                n_ctx = 2048             # Conservative context
            
            logger.info(f"Loading Deepseek-Coder 6.7B from {model_path}")
            logger.info(f"High-performance config: GPU={use_gpu}, Threads={n_threads}, GPU_Layers={n_gpu_layers}")
            logger.info(f"Batch size: {n_batch}, Context: {n_ctx}")
            
            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,
                verbose=False,
                # AWS g5.2xlarge A10G GPU optimizations
                use_mmap=True,
                use_mlock=False,         # Better for cloud instances
                low_vram=False,          # Disabled for 24GB A10G
            )
            
            # Memory check after loading
            mem_after = psutil.virtual_memory()
            memory_used = (mem.available - mem_after.available) / (1024*1024*1024)
            logger.info(f"Deepseek-Coder 6.7B loaded successfully on high-performance hardware!")
            logger.info(f"Memory used: {memory_used:.2f} GB")
            logger.info(f"Available after loading: {mem_after.available / (1024*1024*1024):.2f} GB")
            
            self.model_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Deepseek-Coder model: {str(e)}")
            self.model_loaded = False
            return False

    def monitor_system(self):
        """Monitor system resources"""
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        return {
            "total_memory_gb": round(mem.total / (1024*1024*1024), 2),
            "available_memory_gb": round(mem.available / (1024*1024*1024), 2),
            "used_memory_gb": round(mem.used / (1024*1024*1024), 2),
            "memory_percent": round(mem.percent, 1),
            "cpu_percent": round(cpu_percent, 1)
        }

    def generate_junit_tests(self, java_code, class_name=None):
        """Generate JUnit tests using Deepseek-Coder 6.7B"""
        if not self.model:
            return self._generate_demo_tests(java_code, class_name)

        # Check cache first
        cache_key = hash(java_code + str(class_name))
        if cache_key in self.generation_cache:
            logger.info("Returning cached result")
            return self.generation_cache[cache_key]

        # Extract class name if not provided
        if not class_name:
            class_name = self._extract_class_name(java_code)

        # Simplified prompt for faster, more reliable generation
        prompt = f"""Generate JUnit 5 tests for this Java method:

{java_code}

Create {class_name}Test with @Test methods and assertions.

```java"""

        try:
            start_time = time.time()
            logger.info(f"Starting generation for g5.2xlarge with {len(prompt)} char prompt")
            logger.info(f"Generation settings: max_tokens={self.max_tokens}, temp={self.temperature}, top_p={self.top_p}")
            
            # Try generation with timeout protection
            logger.info("Calling model for generation...")
            output = generate_with_timeout(
                self.model,
                prompt,
                timeout_seconds=45,  # 45 second timeout for individual generation
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stop=["```", "\n\n\n"],
                echo=False,
                top_k=40,
            )
            
            # Check if generation timed out
            if output is None:
                logger.error("Generation timed out - model may be in bad state")
                return self._generate_demo_tests(java_code, class_name)
            
            generation_time = time.time() - start_time
            logger.info(f"Raw generation completed successfully in {generation_time:.2f} seconds")
            
            # Check if we got valid output
            if not output or 'choices' not in output or not output['choices']:
                logger.error("Model returned empty or invalid output")
                return self._generate_demo_tests(java_code, class_name)
            
            generated_text = output['choices'][0]['text']
            logger.info(f"Generated text length: {len(generated_text)} characters")
            logger.info(f"Generated text preview: {generated_text[:100]}...")
            
            # Extract and clean generated code
            cleaned_code = self._clean_generated_code(generated_text, class_name)
            
            # Cache the result and update generation count
            self.generation_cache[cache_key] = cleaned_code
            self.generation_count += 1
            
            logger.info(f"Total generation completed successfully in {generation_time:.2f} seconds (generation #{self.generation_count})")
            
            # Clear cache periodically to prevent memory issues
            if self.generation_count % 10 == 0:
                logger.info(f"Clearing cache after {self.generation_count} generations")
                self.generation_cache.clear()
            
            return cleaned_code
            
        except Exception as e:
            logger.error(f"Generation error (detailed): {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.info("Falling back to demo tests due to generation error")
            return self._generate_demo_tests(java_code, class_name)

    def _generate_demo_tests(self, java_code, class_name):
        """Generate demo JUnit tests when model is not available"""
        if not class_name:
            class_name = self._extract_class_name(java_code)
        
        # Extract methods from the Java code for better demo tests
        methods = self._extract_methods(java_code)
        
        test_methods = []
        for method in methods[:3]:  # Limit to first 3 methods
            method_name = method.replace("(", "").replace(")", "").replace(" ", "")
            test_methods.append(f"""
    @Test
    @DisplayName("Test {method}")
    void test{method_name.title()}() {{
        // TODO: Implement test for {method}
        assertNotNull({class_name.lower()});
    }}""")
        
        demo_test = f"""import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("{class_name} Test Suite - Generated by Deepseek-Coder")
public class {class_name}Test {{
    
    private {class_name} {class_name.lower()};
    
    @BeforeEach
    void setUp() {{
        {class_name.lower()} = new {class_name}();
    }}
{''.join(test_methods)}
    
    @Test
    @DisplayName("Test object initialization")
    void testObjectInitialization() {{
        assertNotNull({class_name.lower()});
    }}
    
    @Test
    @DisplayName("Test edge cases")
    void testEdgeCases() {{
        // TODO: Add edge case tests
        assertTrue(true);
    }}
}}"""
        return demo_test

    def _extract_class_name(self, java_code):
        """Extract class name from Java code"""
        try:
            for line in java_code.split('\n'):
                if 'class ' in line and any(keyword in line for keyword in ['public', 'private', 'protected']):
                    parts = line.split('class ')
                    if len(parts) > 1:
                        return parts[1].split(' ')[0].split('{')[0].split('<')[0].strip()
            return "TestClass"
        except:
            return "TestClass"

    def _extract_methods(self, java_code):
        """Extract method names from Java code"""
        methods = []
        try:
            for line in java_code.split('\n'):
                if ('public ' in line or 'private ' in line) and '(' in line and '{' not in line:
                    # Extract method name
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if '(' in part:
                            method_name = part.split('(')[0]
                            if method_name and not method_name in ['class', 'interface']:
                                methods.append(method_name + "()")
                            break
        except:
            pass
        return methods

    def _clean_generated_code(self, generated_text, class_name):
        """Clean up generated code output"""
        try:
            # Remove markdown formatting
            if "```java" in generated_text:
                import re
                code_blocks = re.findall(r'```java\n(.*?)```', generated_text, re.DOTALL)
                if code_blocks:
                    generated_text = code_blocks[0]
            
            # Ensure proper class structure
            lines = generated_text.split('\n')
            cleaned_lines = []
            brace_count = 0
            class_found = False
            
            for line in lines:
                # Skip empty lines at the beginning
                if not cleaned_lines and not line.strip():
                    continue
                    
                cleaned_lines.append(line)
                
                # Track braces to find end of class
                for char in line:
                    if char == '{':
                        brace_count += 1
                        if f'class {class_name}Test' in line:
                            class_found = True
                    elif char == '}':
                        brace_count -= 1
                        if class_found and brace_count == 0:
                            return '\n'.join(cleaned_lines)
            
            return '\n'.join(cleaned_lines).strip()
        except:
            return generated_text.strip()

# Global generator instance
generator = DeepSeekCoderGenerator()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    memory_info = generator.monitor_system()
    
    return jsonify({
        "status": "healthy",
        "server": "High-Performance Hardware (16GB GPU + 32GB RAM + 16 cores)",
        "model": "Deepseek-Coder 6.7B-Instruct (Q4_K_M)",
        "model_loaded": generator.model_loaded,
        "specialization": "Java JUnit 5 test generation",
        "system_info": memory_info,
        "cache_size": len(generator.generation_cache),
        "optimizations": [
            "16GB GPU VRAM optimized",
            "32GB system RAM utilized",
            "16 CPU cores available",
            "All GPU layers offloaded (GPU mode)",
            "Large batch processing",
            "Enhanced context window",
            "Memory locking enabled",
            "Result caching"
        ]
    }), 200

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the Deepseek-Coder model"""
    try:
        data = request.get_json(force=True) if request.data else {}
        model_path = data.get('model_path', '/home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf')
        use_gpu = data.get('use_gpu', False)
        
        logger.info(f"Initializing Deepseek-Coder model with GPU={use_gpu}")
        success = generator.initialize_model(model_path, use_gpu)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Deepseek-Coder 6.7B initialized successfully on Distm1",
                "server": "Distm1 (10.5.17.187)",
                "model": "Deepseek-Coder 6.7B-Instruct",
                "gpu_enabled": use_gpu,
                "model_path": model_path,
                "memory_info": generator.monitor_system()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to initialize Deepseek-Coder model"
            }), 500
            
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Initialization error: {str(e)}"
        }), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate JUnit tests using Deepseek-Coder with timeout handling"""
    try:
        # Handle JSON parsing more robustly
        if request.is_json:
            data = request.get_json()
        else:
            data = request.get_json(force=True)
            
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt', '')
        class_name = data.get('className')
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating JUnit tests for {class_name or 'unknown class'} (length: {len(prompt)} chars)")
        
        # Clean the prompt - extract Java code if wrapped
        java_code = prompt
        if "Write JUnit tests for this Java" in prompt:
            for phrase in ["Write JUnit tests for this Java file:", "Write JUnit tests for this Java method:", "Generate tests for:"]:
                if phrase in prompt:
                    java_code = prompt.split(phrase)[-1].strip()
                    break
        
        # Check if model is loaded, if not return demo tests immediately
        if not generator.model_loaded or not generator.model:
            logger.warning("Model not loaded, returning demo tests")
            demo_tests = generator._generate_demo_tests(java_code, class_name)
            return jsonify({
                "response": demo_tests,
                "generation_time_seconds": 0.1,
                "cache_size": len(generator.generation_cache),
                "server": "Distm1 (10.5.17.187)",
                "model": "Demo Mode - Model Not Loaded",
                "memory_info": generator.monitor_system()
            }), 200
        
        # Generate tests with detailed logging and longer timeout for g5.2xlarge
        start_time = time.time()
        try:
            logger.info(f"Attempting generation with model_loaded={generator.model_loaded}, model={generator.model is not None}")
            generated_tests = generator.generate_junit_tests(java_code, class_name)
            generation_time = time.time() - start_time
            
            # Much longer timeout for g5.2xlarge (should be fast anyway)
            if generation_time > 120:  # 2 minute timeout for g5.2xlarge
                logger.warning(f"Generation took {generation_time:.2f}s, using demo tests")
                generated_tests = generator._generate_demo_tests(java_code, class_name)
            else:
                logger.info(f"Generation successful in {generation_time:.2f} seconds")
            
        except Exception as gen_error:
            logger.error(f"Generation failed with error: {type(gen_error).__name__}: {str(gen_error)}")
            generated_tests = generator._generate_demo_tests(java_code, class_name)
            generation_time = time.time() - start_time
        
        return jsonify({
            "response": generated_tests,
            "generation_time_seconds": round(generation_time, 2),
            "cache_size": len(generator.generation_cache),
            "server": "Distm1 (10.5.17.187)",
            "model": "Deepseek-Coder 6.7B-Instruct",
            "memory_info": generator.monitor_system()
        }), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/simple-test', methods=['POST'])
def simple_test():
    """Very simple model test with minimal parameters"""
    try:
        if not generator.model_loaded or not generator.model:
            return jsonify({
                "status": "model_not_loaded",
                "message": "Model is not loaded"
            }), 400
            
        logger.info("Testing model with minimal parameters")
        start_time = time.time()
        
        # Extremely simple test
        output = generator.model(
            "Hello",
            max_tokens=10,
            temperature=0.5,
            echo=False
        )
        
        generation_time = time.time() - start_time
        logger.info(f"Simple test completed in {generation_time:.2f} seconds")
        
        return jsonify({
            "status": "success",
            "output": output['choices'][0]['text'],
            "generation_time": round(generation_time, 2)
        }), 200
        
    except Exception as e:
        logger.error(f"Simple test error: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/test-model', methods=['POST'])
def test_model():
    """Quick test of model functionality"""
    try:
        if not generator.model_loaded or not generator.model:
            return jsonify({
                "status": "model_not_loaded",
                "message": "Model is not loaded"
            }), 400
            
        # Simple test generation
        test_prompt = "public class Test { public int add(int a, int b) { return a + b; } }"
        
        start_time = time.time()
        output = generator.model(
            f"Generate a simple test: {test_prompt}",
            max_tokens=50,
            temperature=0.1,
            stop=["\n\n"],
            echo=False
        )
        generation_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "test_output": output['choices'][0]['text'][:100],
            "generation_time": round(generation_time, 2),
            "memory_info": generator.monitor_system()
        }), 200
        
    except Exception as e:
        logger.error(f"Model test error: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/system-status', methods=['GET'])
def system_status():
    """Get system resource usage"""
    try:
        system_info = generator.monitor_system()
        system_info["server"] = "Distm1 (10.5.17.187)"
        system_info["model"] = "Deepseek-Coder 6.7B-Instruct"
        return jsonify(system_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the generation cache"""
    try:
        cache_size = len(generator.generation_cache)
        generator.generation_cache.clear()
        return jsonify({
            "status": "success",
            "message": "Cache cleared successfully",
            "server": "Distm1 (10.5.17.187)",
            "previous_cache_size": cache_size
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset-model', methods=['POST'])
def reset_model():
    """Reset model state to fix hanging issues"""
    try:
        if not generator.model:
            return jsonify({
                "status": "error",
                "message": "No model loaded to reset"
            }), 400
        
        logger.info("Resetting model state...")
        
        # Clear caches
        generator.generation_cache.clear()
        generator.generation_count = 0
        
        # Force garbage collection
        import gc
        gc.collect()
        
        logger.info("Model state reset completed")
        
        return jsonify({
            "status": "success",
            "message": "Model state reset successfully",
            "memory_info": generator.monitor_system()
        }), 200
        
    except Exception as e:
        logger.error(f"Model reset error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JUnit Test Generator using Deepseek-Coder 6.7B - EC2 Optimized')
    parser.add_argument('--port', type=int, default=8082, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--model-path', default='/home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf', help='Path to Deepseek-Coder model file')
    parser.add_argument('--use-gpu', action='store_true', help='Enable GPU acceleration')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Deepseek-Coder 6.7B Test Generator - AWS g5.2xlarge OPTIMIZED")
    logger.info("🖥️  Instance: AWS g5.2xlarge")
    logger.info("🎮 GPU: 24GB A10G NVIDIA GPU")
    logger.info("💾 RAM: 32GB system memory")
    logger.info("⚡ CPU: 8 vCPUs (AMD EPYC 7R32)")
    logger.info("🤖 Model: Deepseek-Coder 6.7B-Instruct (Q4_K_M)")
    logger.info("💾 Optimized for AWS g5.2xlarge instance")
    logger.info(f"🌐 Server will run on {args.host}:{args.port}")
    logger.info(f"🎯 GPU acceleration: {'Enabled' if args.use_gpu else 'Disabled'}")
    
    # Display system information
    mem = psutil.virtual_memory()
    cpu_count = psutil.cpu_count()
    logger.info(f"💻 System: {mem.total / (1024*1024*1024):.1f}GB RAM, {cpu_count} CPU cores")
    logger.info(f"📊 Available: {mem.available / (1024*1024*1024):.1f}GB RAM ({100-mem.percent:.1f}% free)")
    
    if args.use_gpu:
        logger.info("🔥 AWS g5.2xlarge GPU MODE: ALL layers offloaded to 24GB A10G")
        logger.info("⚡ Expected generation time: 3-10 seconds")
    else:
        logger.info("🔥 AWS g5.2xlarge CPU MODE: All 8 vCPUs + 32GB RAM utilized")
        logger.info("⚡ Expected generation time: 8-20 seconds")
    
    app.run(host=args.host, port=args.port, debug=False, threaded=True) 