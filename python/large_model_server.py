#!/usr/bin/env python3
"""
Large Model Server for Test Generation
Uses CodeLlama 7B model for complex file analysis
"""

import argparse
import json
import logging
import torch
import re
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class LargeTestGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.max_length = 16384  # Support longer contexts
    
    def initialize_model(self):
        """Initialize the CodeLlama 7B model with quantization"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            model_name = "codellama/CodeLlama-7b-Instruct-hf"
            logger.info(f"Loading model: {model_name}")
            
            # Use 4-bit quantization to reduce memory usage
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            logger.info("Large model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            return False
    
    def analyze_large_file(self, file_content):
        """Analyze large file and extract key components"""
        # Extract classes
        classes = re.findall(r'(?:public|private|protected)?\s*class\s+(\w+)[^{]*\{', file_content)
        
        # Extract methods with their full signatures
        methods = re.findall(
            r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?{',
            file_content
        )
        
        # Extract imports
        imports = re.findall(r'import\s+([^;]+);', file_content)
        
        # Count complexity indicators
        complexity_indicators = {
            'loops': len(re.findall(r'\b(?:for|while|do)\b', file_content)),
            'conditionals': len(re.findall(r'\b(?:if|else|switch)\b', file_content)),
            'exceptions': len(re.findall(r'\b(?:try|catch|throw|throws)\b', file_content)),
            'annotations': len(re.findall(r'@\w+', file_content)),
            'lines': len(file_content.split('\n'))
        }
        
        return {
            'classes': classes,
            'methods': methods,
            'imports': imports,
            'complexity': complexity_indicators
        }
    
    def chunk_large_file(self, file_content, max_chunk_size=8000):
        """Break large file into manageable chunks for processing"""
        lines = file_content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def generate_comprehensive_tests(self, file_content):
        """Generate comprehensive tests for large files"""
        if self.model is None or self.tokenizer is None:
            raise Exception("Model not initialized")
        
        # Analyze the file structure
        analysis = self.analyze_large_file(file_content)
        logger.info(f"File analysis: {analysis['complexity']}")
        
        # If file is very large, process in chunks
        if analysis['complexity']['lines'] > 1500:
            return self.generate_tests_for_large_file(file_content, analysis)
        else:
            return self.generate_tests_single_pass(file_content, analysis)
    
    def generate_tests_for_large_file(self, file_content, analysis):
        """Handle very large files by processing in chunks"""
        chunks = self.chunk_large_file(file_content, max_chunk_size=6000)
        all_tests = []
        
        logger.info(f"Processing large file in {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Create focused prompt for this chunk
            prompt = f"""You are an expert Java developer. Analyze this code chunk and generate comprehensive JUnit 5 test cases.

Code Chunk {i+1}:
```java
{chunk}
```

Generate complete test classes with:
1. Proper imports
2. Mock setup using Mockito
3. Test methods for each public method
4. Edge cases and error scenarios
5. Proper assertions

Test Code:"""

            try:
                test_code = self.generate_with_model(prompt)
                if test_code and len(test_code.strip()) > 100:
                    all_tests.append(f"// Test for Chunk {i+1}\n{test_code}")
                else:
                    # Fallback for this chunk
                    fallback_test = self.generate_chunk_template(chunk, i+1)
                    all_tests.append(fallback_test)
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                fallback_test = self.generate_chunk_template(chunk, i+1)
                all_tests.append(fallback_test)
        
        # Combine all tests
        combined_tests = "\n\n".join(all_tests)
        
        # Add file summary
        summary = f"""/*
 * Comprehensive Test Suite for Large File
 * 
 * File Statistics:
 * - Lines of code: {analysis['complexity']['lines']}
 * - Classes found: {len(analysis['classes'])}
 * - Methods found: {len(analysis['methods'])}
 * - Complexity indicators: {analysis['complexity']}
 * 
 * Generated in {len(chunks)} chunks
 */

{combined_tests}"""
        
        return summary
    
    def generate_tests_single_pass(self, file_content, analysis):
        """Generate tests for moderately sized files in single pass"""
        prompt = f"""You are an expert Java developer. Analyze this complete Java file and generate comprehensive JUnit 5 test cases.

File Analysis:
- Classes: {analysis['classes']}
- Methods: {len(analysis['methods'])} methods found
- Complexity: {analysis['complexity']}

Java Code:
```java
{file_content[:12000]}  # Limit for model context
```

Generate a complete test suite with:
1. Proper package and imports
2. Test classes for each main class
3. Mock setup using Mockito where needed
4. Comprehensive test methods covering:
   - Happy path scenarios
   - Edge cases
   - Error conditions
   - Boundary values
5. Proper JUnit 5 annotations and assertions

Test Code:"""

        return self.generate_with_model(prompt)
    
    def generate_with_model(self, prompt):
        """Generate using the large model"""
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt", 
            max_length=min(len(prompt) + 2048, self.max_length),
            truncation=True,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part
        if "Test Code:" in generated_text:
            generated_text = generated_text.split("Test Code:")[-1].strip()
        
        return generated_text
    
    def generate_chunk_template(self, chunk, chunk_num):
        """Generate template-based tests for a chunk"""
        # Extract methods from this chunk
        methods = re.findall(r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)', chunk)
        
        test_methods = []
        for method in methods[:5]:  # Limit to 5 methods per chunk
            test_methods.append(f"""
    @Test
    @DisplayName("Test {method} - Chunk {chunk_num}")
    void test{method.capitalize()}Chunk{chunk_num}() {{
        // Arrange
        // TODO: Set up test data for {method}
        
        // Act
        // TODO: Call {method} with test parameters
        
        // Assert
        // TODO: Verify {method} behavior
    }}""")
        
        return f"""
// Tests for Chunk {chunk_num}
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class TestChunk{chunk_num} {{
    
    @BeforeEach
    void setUp() {{
        // Initialize test objects for chunk {chunk_num}
    }}
    
    {"".join(test_methods)}
}}"""

# Global model instance
generator = LargeTestGenerator()

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the large model"""
    try:
        success = generator.initialize_model()
        if success:
            return jsonify({"status": "Large model (CodeLlama 7B) initialized successfully"}), 200
        else:
            return jsonify({"error": "Failed to initialize large model"}), 500
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate test cases for large files"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating tests for content length: {len(prompt)}")
        
        # Extract Java code from prompt
        java_code = prompt
        if "Write JUnit tests for this Java" in prompt:
            # Try to extract code after common prompt phrases
            for phrase in ["Write JUnit tests for this Java file:", "Write JUnit tests for this Java method:", "Generate tests for:"]:
                if phrase in prompt:
                    java_code = prompt.split(phrase)[-1].strip()
                    break
        
        # Generate comprehensive tests
        generated_tests = generator.generate_comprehensive_tests(java_code)
        
        logger.info("Successfully generated comprehensive test suite")
        return jsonify({"response": generated_tests}), 200
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_status = "loaded" if generator.model is not None else "not loaded"
    return jsonify({
        "status": "healthy",
        "model_status": model_status,
        "device": str(generator.device) if generator.device else "unknown",
        "model_type": "CodeLlama 7B",
        "max_context": generator.max_length if generator.max_length else "unknown"
    }), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Large Model Test Generator Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    args = parser.parse_args()
    
    logger.info(f"Starting Large Model Test Generator server on {args.host}:{args.port}")
    logger.info("Using CodeLlama 7B for complex file analysis")
    
    app.run(host=args.host, port=args.port) 