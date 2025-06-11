#!/usr/bin/env python3
"""
Local Test Server for JUnit Generation Testing
Simulates CodeLlama responses for testing purposes
"""

from flask import Flask, request, jsonify
import time
import json

app = Flask(__name__)

# Sample JUnit test template
JUNIT_TEMPLATE = """
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

class {class_name}Test {{

    private {class_name} testObject;

    @BeforeEach
    void setUp() {{
        testObject = new {class_name}();
    }}

    @Test
    void testAdd_WithValidInputs_ShouldReturnSum() {{
        // Arrange
        int a = 5;
        int b = 3;
        
        // Act
        int result = testObject.add(a, b);
        
        // Assert
        assertEquals(8, result);
    }}

    @Test
    void testAdd_WithZeroValues_ShouldReturnCorrectResult() {{
        assertEquals(0, testObject.add(0, 0));
        assertEquals(5, testObject.add(5, 0));
        assertEquals(3, testObject.add(0, 3));
    }}

    @Test
    void testAdd_WithNegativeNumbers_ShouldReturnCorrectResult() {{
        assertEquals(-8, testObject.add(-5, -3));
        assertEquals(2, testObject.add(5, -3));
        assertEquals(-2, testObject.add(-5, 3));
    }}
}}
"""

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": True,
        "model_type": "Local Test Server",
        "model_size": "Simulated",
        "quantization": "N/A",
        "max_tokens": 2048,
        "specialization": "JUnit test generation simulation"
    }), 200

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    time.sleep(1)  # Simulate initialization time
    return jsonify({"status": "Local test model initialized successfully"}), 200

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "No prompt provided"}), 400
        
        prompt = data['prompt']
        
        # Simulate processing time
        time.sleep(2)
        
        # Extract class name from prompt
        class_name = "TestClass"
        if "class " in prompt:
            try:
                class_start = prompt.find("class ") + 6
                class_end = prompt.find(" ", class_start)
                if class_end == -1:
                    class_end = prompt.find("{", class_start)
                class_name = prompt[class_start:class_end].strip()
            except:
                pass
        
        # Generate JUnit test
        generated_test = JUNIT_TEMPLATE.format(class_name=class_name)
        
        return jsonify({"response": generated_test}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/model-info', methods=['GET'])
def model_info():
    return jsonify({
        "model_name": "Local Test Server",
        "model_type": "JUnit generation simulator",
        "parameters": "Simulated",
        "quantization": "N/A",
        "context_length": 4096,
        "temperature": 0.1,
        "capabilities": [
            "JUnit 5 test generation simulation",
            "Fast response for testing",
            "Template-based generation"
        ]
    }), 200

if __name__ == '__main__':
    print("🧪 Starting Local JUnit Test Generation Server")
    print("Server will run on http://localhost:8082")
    print("This simulates CodeLlama responses for testing purposes")
    app.run(host='0.0.0.0', port=8082, debug=False) 