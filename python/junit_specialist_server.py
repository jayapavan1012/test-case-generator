#!/usr/bin/env python3
"""
JUnit Test Generator using llama.cpp
A lightweight and efficient test generator using llama.cpp
"""

import argparse
import json
import logging
from flask import Flask, request, jsonify
from llama_cpp import Llama

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class JUnitTestGenerator:
    def __init__(self):
        self.model = None
        self.max_tokens = 2048
        self.temperature = 0.7
        self.top_p = 0.9
    
    def initialize_model(self, model_path):
        """Initialize llama.cpp model"""
        try:
            logger.info(f"Loading model from {model_path}")
            self.model = Llama(
                model_path=model_path,
                n_ctx=4096,  # Context window
                n_threads=4   # Adjust based on CPU
            )
            logger.info("Model loaded successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

    def generate_tests(self, java_code):
        """Generate JUnit tests using llama.cpp"""
        if not self.model:
            return "Error: Model not initialized"

        # Create a specialized prompt for JUnit test generation
        prompt = f"""Generate comprehensive JUnit 5 tests for the following Java code.
Include proper imports, test class setup, and thorough test cases.

Java code to test:
```java
{java_code}
```

Write complete JUnit 5 tests with:
1. All necessary imports
2. Proper test class structure
3. Test methods for main functionality
4. Edge cases and error scenarios
5. Clear assertions

Generate the test code:"""

        try:
            # Generate using llama.cpp
            output = self.model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                echo=False
            )

            # Extract generated code
            generated_text = output['choices'][0]['text']
            
            # Clean up the output
            if "```java" in generated_text:
                # Extract code from markdown blocks
                import re
                code_blocks = re.findall(r'```java\n(.*?)```', generated_text, re.DOTALL)
                if code_blocks:
                    generated_text = code_blocks[0]
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            return f"Error generating tests: {str(e)}"

# Global generator instance
generator = JUnitTestGenerator()

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the llama.cpp model"""
    try:
        data = request.json or {}
        model_path = data.get('model_path', '/path/to/your/gguf/model.gguf')
        
        success = generator.initialize_model(model_path)
        if success:
            return jsonify({"status": "Model initialized successfully"}), 200
        else:
            return jsonify({"status": "Failed to initialize model"}), 500
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate JUnit tests using llama.cpp"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating JUnit tests for code length: {len(prompt)}")
        
        # Extract Java code from prompt if needed
        java_code = prompt
        if "Write JUnit tests for this Java" in prompt:
            for phrase in ["Write JUnit tests for this Java file:", "Write JUnit tests for this Java method:", "Generate tests for:"]:
                if phrase in prompt:
                    java_code = prompt.split(phrase)[-1].strip()
                    break
        
        # Generate tests
        generated_tests = generator.generate_tests(java_code)
        
        return jsonify({"response": generated_tests}), 200
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": generator.model is not None,
        "model_type": "llama.cpp",
        "max_tokens": generator.max_tokens
    }), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JUnit Test Generator Server using llama.cpp')
    parser.add_argument('--port', type=int, default=8082, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--model-path', default='/path/to/your/gguf/model.gguf', help='Path to the GGUF model file')
    args = parser.parse_args()
    
    logger.info(f"Starting JUnit Test Generator server on {args.host}:{args.port}")
    
    # Initialize model at startup
    if generator.initialize_model(args.model_path):
        logger.info("Model initialized successfully")
    else:
        logger.warning("Failed to initialize model, starting server anyway")
    
    app.run(host=args.host, port=args.port) 