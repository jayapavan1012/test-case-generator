#!/usr/bin/env python3
"""
Local Model Server for Test Generation
Uses CodeT5+ model loaded locally
"""

import argparse
import json
import logging
import torch
from flask import Flask, request, jsonify
from transformers import T5ForConditionalGeneration, RobertaTokenizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class LocalTestGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
    
    def initialize_model(self):
        """Initialize the CodeT5+ model"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            model_name = "Salesforce/codet5p-220m"  # Smaller CodeT5+ model (~220MB)
            logger.info(f"Loading model: {model_name}")
            
            # Load tokenizer and model
            self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            if not torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            return False
    
    def generate_test(self, java_code):
        """Generate test code using the local model"""
        if self.model is None or self.tokenizer is None:
            raise Exception("Model not initialized")
        
        # Prepare prompt for CodeT5+
        prompt = f"Generate JUnit test cases for the following Java method:\n\n{java_code}\n\nTest cases:"
        
        # Tokenize input
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
        inputs = inputs.to(self.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=1024,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode response
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up the response (remove the input prompt)
        if "Test cases:" in generated_text:
            generated_text = generated_text.split("Test cases:")[-1].strip()
        
        return generated_text

# Global model instance
generator = LocalTestGenerator()

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the local model"""
    try:
        success = generator.initialize_model()
        if success:
            return jsonify({"status": "Local model initialized successfully"}), 200
        else:
            return jsonify({"error": "Failed to initialize model"}), 500
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate test cases using the local model"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating tests for code length: {len(prompt)}")
        
        # Extract Java code from prompt
        java_code = prompt
        if "Write JUnit tests for this Java method:" in prompt:
            java_code = prompt.split("Write JUnit tests for this Java method:")[-1].strip()
        
        # Generate test using local model
        generated_test = generator.generate_test(java_code)
        
        # If the model output is too short or doesn't look like a test, use template fallback
        if len(generated_test.strip()) < 50 or "test" not in generated_test.lower():
            logger.info("Model output insufficient, using template fallback")
            fallback_test = generate_template_test(java_code)
            return jsonify({"response": fallback_test}), 200
        
        logger.info("Successfully generated test using local model")
        return jsonify({"response": generated_test}), 200
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        # Use template fallback on error
        try:
            java_code = data.get('prompt', '')
            if "Write JUnit tests for this Java method:" in java_code:
                java_code = java_code.split("Write JUnit tests for this Java method:")[-1].strip()
            fallback_test = generate_template_test(java_code)
            return jsonify({"response": fallback_test}), 200
        except:
            return jsonify({"error": str(e)}), 500

def generate_template_test(java_code):
    """Fallback template-based test generation"""
    import re
    
    # Extract method name
    method_match = re.search(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', java_code)
    method_name = method_match.group(1) if method_match else "testMethod"
    
    # Extract return type
    return_match = re.search(r'public\s+(\w+)\s+\w+\s*\([^)]*\)', java_code)
    return_type = return_match.group(1) if return_match else "void"
    
    template = f"""
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class {method_name.capitalize()}Test {{
    
    @BeforeEach
    void setUp() {{
        // Initialize test objects
    }}
    
    @Test
    @DisplayName("Test {method_name} with valid input")
    void test{method_name.capitalize()}WithValidInput() {{
        // Arrange
        // TODO: Set up test data
        
        // Act
        {return_type + " result = " if return_type != "void" else ""}classUnderTest.{method_name}(/* test parameters */);
        
        // Assert
        {"assertNotNull(result);" if return_type != "void" else "// Verify method executed successfully"}
    }}
    
    @Test
    @DisplayName("Test {method_name} with edge cases")
    void test{method_name.capitalize()}WithEdgeCases() {{
        // TODO: Add edge case tests
    }}
    
    @Test
    @DisplayName("Test {method_name} with invalid input")
    void test{method_name.capitalize()}WithInvalidInput() {{
        // TODO: Add negative test cases
    }}
}}
"""
    return template.strip()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_status = "loaded" if generator.model is not None else "not loaded"
    return jsonify({
        "status": "healthy",
        "model_status": model_status,
        "device": str(generator.device) if generator.device else "unknown"
    }), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Local Model Test Generator Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    args = parser.parse_args()
    
    logger.info(f"Starting Local Model Test Generator server on {args.host}:{args.port}")
    logger.info("Using CodeT5+ model locally")
    
    app.run(host=args.host, port=args.port) 