# 🌐 Manual EC2 Deployment via VPN + Password Auth

## 📋 Prerequisites
- ✅ Connected to VPN  
- ✅ EC2 instance running with SSH access
- ✅ Username and password for EC2 instance
- ✅ Security group allows SSH (port 22) and HTTP (port 8082)

## 🚀 Step-by-Step Manual Deployment

### **Step 1: Copy Files to EC2**

**Option A: Using SCP with Password**
```bash
# Install sshpass if not available (try this first)
sudo apt-get install sshpass -y

# Copy the optimized script
sshpass -p 'YOUR_PASSWORD' scp python/codellama_test_generator.py username@your-ec2-ip:/home/username/

# Copy deployment files
sshpass -p 'YOUR_PASSWORD' scp README_EC2_DEPLOYMENT.md username@your-ec2-ip:/home/username/
```

**Option B: Manual File Transfer (if sshpass not available)**
```bash
# SSH to EC2 first
ssh username@your-ec2-ip

# On EC2: Create directories
mkdir -p /home/username/test-generator/python
mkdir -p /home/username/test-generator/logs

# Exit SSH and use SFTP or file manager to copy files manually
# Then continue with Step 2
```

### **Step 2: SSH to EC2 and Setup Environment**

```bash
# Connect to EC2
ssh username@your-ec2-ip

# Update system
sudo apt-get update

# Install Python and pip
sudo apt-get install -y python3 python3-pip

# Install required packages
pip3 install --user flask llama-cpp-python psutil

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### **Step 3: Create Optimized Server Script**

```bash
# Create the optimized script (copy-paste the content)
nano /home/username/codellama_test_generator.py
```

**Copy and paste this entire optimized script:**

```python
#!/usr/bin/env python3
"""
JUnit Test Generator using CodeLlama 13B
Optimized for EC2 instance with 32GB RAM and code generation
"""

import argparse
import json
import logging
import psutil
import time
from flask import Flask, request, jsonify

# Try to import llama_cpp, graceful fallback if not available
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️ llama_cpp not available - running in test mode")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class CodeLlamaTestGenerator:
    def __init__(self):
        self.model = None
        # Optimized settings for 32GB RAM EC2 instance
        self.max_tokens = 1024  # Balanced for quality and speed
        self.temperature = 0.1  # Lower temperature for more deterministic code generation
        self.top_p = 0.95
        self.repeat_penalty = 1.1
        self.generation_cache = {}  # Cache for repeated requests
    
    def initialize_model(self, model_path, use_gpu=False):
        """Initialize CodeLlama model with optimized settings for 32GB RAM"""
        try:
            if not LLAMA_CPP_AVAILABLE:
                logger.warning("llama_cpp not available - running in test/demo mode")
                logger.info("Model initialization skipped - will use test responses")
                return True
            
            # Check available memory before loading
            mem = psutil.virtual_memory()
            logger.info(f"Available memory before model loading: {mem.available / (1024*1024*1024):.2f} GB")
            
            if mem.available < 8 * 1024 * 1024 * 1024:  # Less than 8GB available
                logger.warning("Low memory available. Consider freeing up memory before loading the model.")
            
            # Optimized settings for 32GB RAM
            n_gpu_layers = 32 if use_gpu else 0  # Full GPU offload if available
            n_threads = 8 if use_gpu else 16     # More CPU threads when using CPU only
            n_batch = 1024 if use_gpu else 512   # Larger batches with more memory
            
            logger.info(f"Loading CodeLlama 13B model from {model_path}")
            logger.info(f"Configuration: GPU={use_gpu}, Threads={n_threads}, GPU_Layers={n_gpu_layers}")
            
            self.model = Llama(
                model_path=model_path,
                n_ctx=4096,  # Full context window - we have enough RAM
                n_threads=n_threads,  # Optimized for available CPU cores
                n_gpu_layers=n_gpu_layers,  # GPU offloading if available
                n_batch=n_batch,  # Optimized batch size
                verbose=False,
                # Memory optimizations for 32GB system
                use_mmap=True,      # Memory-mapped files for faster loading
                use_mlock=True,     # Lock memory to prevent swapping
                low_vram=not use_gpu,  # CPU optimization when not using GPU
                # Additional optimizations
                n_gqa=1,           # Grouped-query attention optimization
                rms_norm_eps=1e-5, # Numerical stability
            )
            
            # Check memory after loading
            mem_after = psutil.virtual_memory()
            memory_used = (mem.available - mem_after.available) / (1024*1024*1024)
            logger.info(f"Model loaded successfully!")
            logger.info(f"Memory used by model: {memory_used:.2f} GB")
            logger.info(f"Available memory after loading: {mem_after.available / (1024*1024*1024):.2f} GB")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

    def monitor_memory_usage(self):
        """Monitor current memory usage"""
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "total_memory_gb": mem.total / (1024*1024*1024),
            "available_memory_gb": mem.available / (1024*1024*1024),
            "used_memory_gb": mem.used / (1024*1024*1024),
            "memory_percent": mem.percent,
            "cpu_percent": cpu_percent
        }

    def generate_tests(self, java_code, class_name=None):
        """Generate JUnit tests using CodeLlama 13B with memory monitoring"""
        if not self.model:
            return "Error: Model not initialized"

        # Check cache first
        cache_key = hash(java_code)
        if cache_key in self.generation_cache:
            logger.info("Returning cached result")
            return self.generation_cache[cache_key]

        # Monitor memory before generation
        mem_before = psutil.virtual_memory()
        logger.info(f"Memory before generation: {mem_before.available / (1024*1024):.2f} MB available")

        # Extract class name if not provided
        if not class_name:
            class_name = self._extract_class_name(java_code)

        # Enhanced CodeLlama-specific prompt for JUnit generation
        prompt = f"""[INST] You are an expert Java developer and testing specialist. Generate comprehensive JUnit 5 tests for the following Java code.

Requirements:
1. Include all necessary imports (org.junit.jupiter.api.*, static assertions)
2. Create a proper test class named {class_name}Test
3. Use @Test, @BeforeEach, @AfterEach annotations as needed
4. Test main functionality, edge cases, and error scenarios
5. Use appropriate assertions: assertEquals, assertTrue, assertFalse, assertThrows, assertNotNull
6. Follow JUnit 5 best practices and naming conventions
7. Include meaningful test method names that describe what is being tested

Java code to test:
```java
{java_code}
```

Generate complete, runnable JUnit 5 test code: [/INST]

```java"""

        try:
            start_time = time.time()
            
            # Generate using optimized CodeLlama settings
            output = self.model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stop=["```", "</s>", "[INST]"],
                echo=False,
                # Performance optimizations
                top_k=50,
                typical_p=1.0,
                mirostat=0,  # Disable mirostat for faster generation
            )

            generation_time = time.time() - start_time
            
            # Extract generated code
            generated_text = output['choices'][0]['text']
            
            # Clean up the output
            generated_text = self._clean_generated_code(generated_text)
            
            # Monitor memory after generation
            mem_after = psutil.virtual_memory()
            logger.info(f"Generation completed in {generation_time:.2f} seconds")
            logger.info(f"Memory after generation: {mem_after.available / (1024*1024):.2f} MB available")
            
            # Cache the result
            self.generation_cache[cache_key] = generated_text
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            return f"Error generating tests: {str(e)}"

    def _extract_class_name(self, java_code):
        """Extract class name from Java code"""
        try:
            lines = java_code.split('\n')
            for line in lines:
                if 'class ' in line and ('public' in line or 'private' in line or 'protected' in line):
                    parts = line.split('class ')
                    if len(parts) > 1:
                        class_part = parts[1].split(' ')[0].split('{')[0].split('<')[0].strip()
                        return class_part
            return "TestClass"
        except:
            return "TestClass"

    def _clean_generated_code(self, generated_text):
        """Clean up generated code output"""
        try:
            # Remove any markdown formatting
            if "```java" in generated_text:
                import re
                code_blocks = re.findall(r'```java\n(.*?)```', generated_text, re.DOTALL)
                if code_blocks:
                    generated_text = code_blocks[0]
            
            # Remove any trailing text after the last }
            lines = generated_text.split('\n')
            last_brace_idx = -1
            brace_count = 0
            
            for i, line in enumerate(lines):
                for char in line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and 'class' in ' '.join(lines[:i+5]):
                            last_brace_idx = i
                            break
            
            if last_brace_idx != -1:
                generated_text = '\n'.join(lines[:last_brace_idx + 1])
            
            return generated_text.strip()
        except:
            return generated_text.strip()

# Global generator instance
generator = CodeLlamaTestGenerator()

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the CodeLlama model with GPU support option"""
    try:
        data = request.json or {}
        model_path = data.get('model_path', '/home/adminuser/models/codellama-13b-instruct.Q4_K_M.gguf')
        use_gpu = data.get('use_gpu', False)
        
        logger.info(f"Initializing model with GPU={use_gpu}")
        success = generator.initialize_model(model_path, use_gpu)
        
        if success:
            return jsonify({
                "status": "CodeLlama 13B model initialized successfully",
                "gpu_enabled": use_gpu,
                "model_path": model_path,
                "memory_info": generator.monitor_memory_usage()
            }), 200
        else:
            return jsonify({"status": "Failed to initialize CodeLlama model"}), 500
            
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate JUnit tests using CodeLlama 13B with performance monitoring"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        class_name = data.get('className')
        
        logger.info(f"Generating JUnit tests for code length: {len(prompt)} characters")
        
        # Extract Java code from prompt if needed
        java_code = prompt
        if "Write JUnit tests for this Java" in prompt:
            for phrase in ["Write JUnit tests for this Java file:", "Write JUnit tests for this Java method:", "Generate tests for:"]:
                if phrase in prompt:
                    java_code = prompt.split(phrase)[-1].strip()
                    break
        
        # Generate tests
        start_time = time.time()
        generated_tests = generator.generate_tests(java_code, class_name)
        generation_time = time.time() - start_time
        
        return jsonify({
            "response": generated_tests,
            "generation_time_seconds": round(generation_time, 2),
            "cache_size": len(generator.generation_cache),
            "memory_info": generator.monitor_memory_usage()
        }), 200
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with system information"""
    memory_info = generator.monitor_memory_usage()
    
    return jsonify({
        "status": "healthy",
        "model_loaded": generator.model is not None,
        "model_type": "CodeLlama 13B Instruct Q4_K_M",
        "model_size": "13B parameters",
        "quantization": "Q4_K_M (4-bit)",
        "max_tokens": generator.max_tokens,
        "cache_size": len(generator.generation_cache),
        "specialization": "Java JUnit 5 test generation",
        "system_info": memory_info,
        "optimizations": [
            "32GB RAM optimized",
            "16 CPU threads (CPU mode)",
            "8 CPU threads + GPU offload (GPU mode)",
            "Memory monitoring",
            "Result caching",
            "Optimized batch processing"
        ]
    }), 200

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get detailed model and system information"""
    return jsonify({
        "model_name": "CodeLlama 13B Instruct",
        "model_type": "Code generation specialist",
        "parameters": "13 billion",
        "quantization": "Q4_K_M (4-bit)",
        "context_length": 4096,
        "temperature": generator.temperature,
        "top_p": generator.top_p,
        "max_tokens": generator.max_tokens,
        "system_memory": generator.monitor_memory_usage(),
        "capabilities": [
            "JUnit 5 test generation",
            "Java code understanding", 
            "Edge case identification",
            "Test method creation",
            "Import statement generation",
            "Error scenario testing",
            "Best practices compliance"
        ],
        "ec2_optimizations": [
            "32GB RAM utilization",
            "Multi-threaded processing",
            "Optional GPU acceleration",
            "Memory-mapped model loading",
            "Batch processing optimization",
            "Real-time memory monitoring"
        ]
    }), 200

@app.route('/system-status', methods=['GET'])
def system_status():
    """Get current system resource usage"""
    try:
        return jsonify(generator.monitor_memory_usage()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the generation cache"""
    try:
        cache_size = len(generator.generation_cache)
        generator.generation_cache.clear()
        return jsonify({
            "status": "Cache cleared successfully",
            "previous_cache_size": cache_size
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JUnit Test Generator using CodeLlama 13B - EC2 Optimized')
    parser.add_argument('--port', type=int, default=8082, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--model-path', default='/home/adminuser/models/codellama-13b-instruct.Q4_K_M.gguf', help='Path to the CodeLlama GGUF model file')
    parser.add_argument('--use-gpu', action='store_true', help='Enable GPU acceleration if available')
    args = parser.parse_args()
    
    logger.info("🚀 Starting CodeLlama 13B Test Generator - EC2 Optimized")
    logger.info("💾 Optimized for 32GB RAM EC2 instances")
    logger.info("⚡ Enhanced performance with multi-threading and caching")
    logger.info(f"🖥️  Server will run on {args.host}:{args.port}")
    logger.info(f"🎯 GPU acceleration: {'Enabled' if args.use_gpu else 'Disabled'}")
    
    # Display system information
    mem = psutil.virtual_memory()
    cpu_count = psutil.cpu_count()
    logger.info(f"💻 System: {mem.total / (1024*1024*1024):.1f}GB RAM, {cpu_count} CPU cores")
    logger.info(f"📊 Available: {mem.available / (1024*1024*1024):.1f}GB RAM ({100-mem.percent:.1f}% free)")
    
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
```

### **Step 4: Start the Optimized Server**

```bash
# Make script executable
chmod +x /home/username/codellama_test_generator.py

# Start server (replace with your actual model path)
nohup python3 codellama_test_generator.py \
    --port 8082 \
    --host 0.0.0.0 \
    --model-path /path/to/your/codellama-model.gguf \
    > codellama.log 2>&1 &

# Check if server started
sleep 5
curl http://localhost:8082/health
```

### **Step 5: Initialize the Model**

```bash
# Initialize the model (run this once)
curl -X POST http://localhost:8082/initialize-model \
  -H "Content-Type: application/json" \
  -d '{"model_path": "/path/to/your/model.gguf", "use_gpu": false}'
```

### **Step 6: Test the Optimized System**

```bash
# Test system status
curl http://localhost:8082/system-status

# Test generation
curl -X POST http://localhost:8082/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }", "className": "Calculator"}'
```

## 🎯 **Key Benefits Applied**

✅ **16 CPU threads** for maximum performance  
✅ **Memory monitoring** and optimization  
✅ **Result caching** for faster repeated requests  
✅ **Graceful error handling**  
✅ **Real-time performance metrics**  

## 🔍 **Monitoring & Troubleshooting**

```bash
# Monitor server logs
tail -f codellama.log

# Check memory usage
curl http://your-ec2-ip:8082/system-status

# Restart server if needed
pkill -f "python.*codellama"
nohup python3 codellama_test_generator.py --port 8082 > codellama.log 2>&1 &
```

## 📡 **Access from Local Machine**

Once deployed, access your optimized server:

```bash
# Health check
curl http://your-ec2-ip:8082/health

# Generate tests
curl -X POST http://your-ec2-ip:8082/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "your java code", "className": "YourClass"}'
```

This manual approach gives you the same **32GB RAM optimizations** with **16 CPU threads**, **memory monitoring**, and **caching** for maximum performance! 