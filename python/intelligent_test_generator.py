#!/usr/bin/env python3
"""
Intelligent Test Generator for Large Files
Uses chunking strategies and code analysis for complex files
"""

import argparse
import json
import logging
import torch
import re
import ast
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class IntelligentTestGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.max_context = 4096
    
    def initialize_model(self):
        """Initialize a reliable code generation model"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # Use CodeT5+ 770M - larger than 220M but more manageable than 7B
            model_name = "Salesforce/codet5p-770m"
            logger.info(f"Loading model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            if not torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            # Fallback to smaller model
            try:
                model_name = "Salesforce/codet5p-220m"
                logger.info(f"Fallback to: {model_name}")
                
                from transformers import RobertaTokenizer, T5ForConditionalGeneration
                self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
                self.model = T5ForConditionalGeneration.from_pretrained(model_name)
                
                if not torch.cuda.is_available():
                    self.model = self.model.to(self.device)
                
                logger.info("Fallback model loaded successfully")
                return True
            except Exception as fallback_error:
                logger.error(f"Fallback failed: {str(fallback_error)}")
                return False
    
    def analyze_java_file(self, file_content):
        """Comprehensive Java file analysis"""
        analysis = {
            'classes': [],
            'methods': [],
            'interfaces': [],
            'enums': [],
            'imports': [],
            'package': None,
            'annotations': [],
            'complexity_score': 0,
            'line_count': len(file_content.split('\n')),
            'dependencies': set()
        }
        
        # Extract package
        package_match = re.search(r'package\s+([^;]+);', file_content)
        if package_match:
            analysis['package'] = package_match.group(1).strip()
        
        # Extract imports
        imports = re.findall(r'import\s+(?:static\s+)?([^;]+);', file_content)
        analysis['imports'] = imports
        for imp in imports:
            analysis['dependencies'].add(imp.split('.')[0])
        
        # Extract classes with details
        class_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{'
        for match in re.finditer(class_pattern, file_content):
            class_info = {
                'name': match.group(1),
                'extends': match.group(2) if match.group(2) else None,
                'implements': [i.strip() for i in match.group(3).split(',')] if match.group(3) else [],
                'start_pos': match.start(),
                'methods': []
            }
            analysis['classes'].append(class_info)
        
        # Extract interfaces
        interface_pattern = r'(?:public|private|protected)?\s*interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{'
        for match in re.finditer(interface_pattern, file_content):
            analysis['interfaces'].append({
                'name': match.group(1),
                'extends': [i.strip() for i in match.group(2).split(',')] if match.group(2) else []
            })
        
        # Extract methods with detailed information
        method_pattern = r'((?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:abstract\s+)?(?:<[^>]+>\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)(?:\s+throws\s+[^{]+)?\s*\{)'
        for match in re.finditer(method_pattern, file_content):
            method_info = {
                'visibility': self._extract_visibility(match.group(1)),
                'return_type': match.group(2),
                'name': match.group(3),
                'parameters': self._parse_parameters(match.group(4)),
                'full_signature': match.group(0),
                'start_pos': match.start(),
                'is_static': 'static' in match.group(1),
                'is_abstract': 'abstract' in match.group(1)
            }
            analysis['methods'].append(method_info)
        
        # Calculate complexity score
        analysis['complexity_score'] = self._calculate_complexity(file_content)
        
        # Extract annotations
        analysis['annotations'] = re.findall(r'@(\w+)', file_content)
        
        return analysis
    
    def _extract_visibility(self, method_signature):
        """Extract visibility modifier"""
        if 'public' in method_signature:
            return 'public'
        elif 'private' in method_signature:
            return 'private'
        elif 'protected' in method_signature:
            return 'protected'
        else:
            return 'package'
    
    def _parse_parameters(self, params_str):
        """Parse method parameters"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if param:
                parts = param.split()
                if len(parts) >= 2:
                    params.append({
                        'type': ' '.join(parts[:-1]),
                        'name': parts[-1]
                    })
        return params
    
    def _calculate_complexity(self, content):
        """Calculate complexity score based on various factors"""
        score = 0
        score += len(re.findall(r'\bif\b|\belse\b|\bswitch\b', content)) * 2
        score += len(re.findall(r'\bfor\b|\bwhile\b|\bdo\b', content)) * 3
        score += len(re.findall(r'\btry\b|\bcatch\b|\bfinally\b', content)) * 2
        score += len(re.findall(r'\bthrow\b|\bthrows\b', content)) * 1
        score += len(re.findall(r'@\w+', content)) * 1
        score += len(re.findall(r'\bsynchronized\b|\bvolatile\b', content)) * 2
        return score
    
    def chunk_by_methods(self, file_content, analysis, max_chunk_size=3000):
        """Intelligently chunk file by methods and classes"""
        chunks = []
        lines = file_content.split('\n')
        
        # Sort methods by position
        methods = sorted(analysis['methods'], key=lambda m: m['start_pos'])
        classes = sorted(analysis['classes'], key=lambda c: c['start_pos'])
        
        current_chunk = []
        current_size = 0
        chunk_metadata = []
        
        # Include imports and package in first chunk
        imports_section = []
        for i, line in enumerate(lines):
            if line.strip().startswith('package') or line.strip().startswith('import') or not line.strip():
                imports_section.append(line)
            else:
                break
        
        if imports_section:
            imports_text = '\n'.join(imports_section)
            chunks.append({
                'content': imports_text,
                'type': 'imports',
                'metadata': {'imports': analysis['imports'], 'package': analysis['package']}
            })
        
        # Process each class separately
        for class_info in classes:
            class_methods = [m for m in methods if m['start_pos'] > class_info['start_pos']]
            
            # Extract class content
            class_start = class_info['start_pos']
            next_class_start = None
            for other_class in classes:
                if other_class['start_pos'] > class_start:
                    next_class_start = other_class['start_pos']
                    break
            
            class_end = next_class_start if next_class_start else len(file_content)
            class_content = file_content[class_start:class_end]
            
            if len(class_content) > max_chunk_size:
                # Split large class into method chunks
                method_chunks = self._chunk_class_by_methods(class_content, class_methods, max_chunk_size)
                for chunk in method_chunks:
                    chunks.append({
                        'content': chunk['content'],
                        'type': 'class_methods',
                        'metadata': {
                            'class_name': class_info['name'],
                            'methods': chunk['methods']
                        }
                    })
            else:
                chunks.append({
                    'content': class_content,
                    'type': 'class',
                    'metadata': {
                        'class_name': class_info['name'],
                        'methods': [m['name'] for m in class_methods if m['start_pos'] < class_end]
                    }
                })
        
        return chunks
    
    def _chunk_class_by_methods(self, class_content, methods, max_size):
        """Chunk a large class by its methods"""
        chunks = []
        lines = class_content.split('\n')
        
        # Find class header
        class_header = []
        brace_count = 0
        for i, line in enumerate(lines):
            class_header.append(line)
            if '{' in line:
                brace_count += line.count('{')
                if brace_count > 0:
                    break
        
        current_chunk = class_header[:]
        current_methods = []
        
        # Add methods to chunks
        for method in methods[:10]:  # Limit methods per chunk
            method_lines = method['full_signature'].split('\n')
            if len('\n'.join(current_chunk + method_lines)) > max_size and current_chunk != class_header:
                # Finalize current chunk
                current_chunk.append('}')  # Close class
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'methods': current_methods[:]
                })
                current_chunk = class_header[:]
                current_methods = []
            
            current_chunk.extend(method_lines)
            current_methods.append(method['name'])
        
        # Add remaining chunk
        if len(current_chunk) > len(class_header):
            current_chunk.append('}')
            chunks.append({
                'content': '\n'.join(current_chunk),
                'methods': current_methods
            })
        
        return chunks
    
    def generate_comprehensive_tests(self, file_content):
        """Generate comprehensive tests for large files"""
        # Analyze the file
        analysis = self.analyze_java_file(file_content)
        logger.info(f"File analysis: {analysis['line_count']} lines, {len(analysis['classes'])} classes, {len(analysis['methods'])} methods, complexity: {analysis['complexity_score']}")
        
        if analysis['line_count'] > 1500:
            return self._generate_for_large_file(file_content, analysis)
        else:
            return self._generate_for_medium_file(file_content, analysis)
    
    def _generate_for_large_file(self, file_content, analysis):
        """Handle very large files with intelligent chunking"""
        chunks = self.chunk_by_methods(file_content, analysis, max_chunk_size=3000)
        
        logger.info(f"Processing large file in {len(chunks)} intelligent chunks")
        
        test_files = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk['type']}")
            
            if chunk['type'] == 'imports':
                continue  # Skip imports chunk for test generation
            
            try:
                if self.model is not None:
                    test_code = self._generate_with_model(chunk, analysis)
                else:
                    test_code = None
                
                if not test_code or len(test_code.strip()) < 100:
                    test_code = self._generate_template_for_chunk(chunk, analysis)
                
                test_files.append({
                    'type': chunk['type'],
                    'metadata': chunk['metadata'],
                    'test_code': test_code
                })
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                fallback_test = self._generate_template_for_chunk(chunk, analysis)
                test_files.append({
                    'type': chunk['type'],
                    'metadata': chunk['metadata'],
                    'test_code': fallback_test
                })
        
        # Combine all test files
        return self._combine_test_files(test_files, analysis)
    
    def _generate_for_medium_file(self, file_content, analysis):
        """Handle medium-sized files in single pass"""
        try:
            if self.model is not None:
                return self._generate_with_model_single_pass(file_content, analysis)
            else:
                return self._generate_comprehensive_template(file_content, analysis)
        except Exception as e:
            logger.error(f"Error in medium file generation: {str(e)}")
            return self._generate_comprehensive_template(file_content, analysis)
    
    def _generate_with_model(self, chunk, analysis):
        """Generate tests using the model for a chunk"""
        prompt = f"""Generate comprehensive JUnit 5 test cases for this Java code chunk.

Code Type: {chunk['type']}
Metadata: {chunk['metadata']}

Java Code:
```java
{chunk['content'][:2000]}  # Limit context
```

Requirements:
1. Use JUnit 5 annotations
2. Include Mockito for mocking
3. Test all public methods
4. Include edge cases and error scenarios
5. Proper assertions

Test Code:"""

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=2048, truncation=True)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract generated part
            if "Test Code:" in generated:
                generated = generated.split("Test Code:")[-1].strip()
            
            return generated
        except Exception as e:
            logger.error(f"Model generation error: {str(e)}")
            return None
    
    def _generate_template_for_chunk(self, chunk, analysis):
        """Generate template-based tests for a chunk"""
        if chunk['type'] == 'class':
            return self._generate_class_template(chunk, analysis)
        else:
            return self._generate_methods_template(chunk, analysis)
    
    def _generate_class_template(self, chunk, analysis):
        """Generate template tests for a whole class"""
        class_name = chunk['metadata']['class_name']
        methods = chunk['metadata']['methods']
        
        test_methods = []
        for method in methods[:8]:  # Limit methods
            test_methods.append(f"""
    @Test
    @DisplayName("Test {method} - happy path")
    void test{method.capitalize()}HappyPath() {{
        // Arrange
        // TODO: Set up test data for {method}
        
        // Act
        // TODO: Call {method} with valid parameters
        
        // Assert
        // TODO: Verify expected behavior
    }}
    
    @Test
    @DisplayName("Test {method} - edge cases")
    void test{method.capitalize()}EdgeCases() {{
        // TODO: Test edge cases for {method}
    }}""")
        
        package_import = f"package {analysis['package']}.test;" if analysis['package'] else ""
        
        return f"""{package_import}

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class {class_name}Test {{
    
    private {class_name} {class_name.lower()};
    
    @BeforeEach
    void setUp() {{
        {class_name.lower()} = new {class_name}();
    }}
    
    {"".join(test_methods)}
}}"""
    
    def _generate_comprehensive_template(self, file_content, analysis):
        """Generate comprehensive template-based tests"""
        all_tests = []
        
        for class_info in analysis['classes']:
            class_tests = self._generate_class_template(
                {
                    'metadata': {
                        'class_name': class_info['name'],
                        'methods': [m['name'] for m in analysis['methods'] if m['start_pos'] > class_info['start_pos']][:10]
                    }
                },
                analysis
            )
            all_tests.append(class_tests)
        
        return "\n\n".join(all_tests)
    
    def _combine_test_files(self, test_files, analysis):
        """Combine multiple test files into a comprehensive suite"""
        combined = f"""/*
 * Comprehensive Test Suite
 * Generated for large file with {analysis['line_count']} lines
 * Classes: {len(analysis['classes'])}
 * Methods: {len(analysis['methods'])}
 * Complexity Score: {analysis['complexity_score']}
 */

"""
        
        for test_file in test_files:
            combined += f"\n// === {test_file['type'].upper()} TESTS ===\n"
            combined += test_file['test_code']
            combined += "\n\n"
        
        return combined

# Global generator instance
generator = IntelligentTestGenerator()

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the intelligent model"""
    try:
        success = generator.initialize_model()
        if success:
            return jsonify({"status": "Intelligent test generator initialized successfully"}), 200
        else:
            return jsonify({"status": "Template-only mode (model failed to load)"}), 200
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({"status": "Template-only mode", "error": str(e)}), 200

@app.route('/generate', methods=['POST'])
def generate():
    """Generate comprehensive tests for large files"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating tests for content length: {len(prompt)}")
        
        # Extract Java code
        java_code = prompt
        if "Write JUnit tests for this Java" in prompt:
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
    model_status = "loaded" if generator.model is not None else "template-only"
    return jsonify({
        "status": "healthy",
        "model_status": model_status,
        "device": str(generator.device) if generator.device else "cpu",
        "model_type": "Intelligent CodeT5+ with fallback",
        "max_context": generator.max_context
    }), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Intelligent Test Generator Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    args = parser.parse_args()
    
    logger.info(f"Starting Intelligent Test Generator server on {args.host}:{args.port}")
    logger.info("Using intelligent chunking and analysis for large files")
    
    app.run(host=args.host, port=args.port) 