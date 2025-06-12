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
import re

# Import with graceful fallback
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Optimized logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeepSeekV2Generator:
    """
    A class to handle JUnit test generation using Deepseek Coder models.
    It uses Deepseek-V2 via Ollama as the primary model and can fall back
    to a local 6.7B GGUF model if specified.
    """
    
    def __init__(self, ollama_base_url="http://localhost:11434", deepseek_model_name="deepseek-coder-v2:16b"):
        # Primary Ollama Deepseek-V2 model
        self.ollama_base_url = ollama_base_url
        self.ollama_api_url = f"{ollama_base_url}/api/generate"
        self.deepseek_v2_model_name = deepseek_model_name
        self.deepseek_v2_available = False
        
        # Fallback local Llama-cpp model
        self.llm = None
        self.deepseek_6b_initialized = False
        
        # Check for Deepseek-V2 availability on init
        self.deepseek_v2_available = self.check_deepseek_v2_status()
        if not self.deepseek_v2_available:
            logger.warning("Deepseek-V2 model not found on Ollama. The app will rely on the fallback model.")
            logger.warning("Ensure Ollama is running and you have pulled the 'deepseek-coder-v2' model.")

    def check_deepseek_v2_status(self):
        """Checks if the Deepseek-V2 model is available on the Ollama server."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get('models', [])
            for model in models:
                if self.deepseek_v2_model_name in model['name']:
                    logger.info(f"Found Deepseek-V2 model on Ollama: {model['name']}")
                    return True
            logger.warning(f"Ollama is running, but '{self.deepseek_v2_model_name}' not found.")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not connect to Ollama at {self.ollama_base_url}. Error: {e}")
            return False
    
    def generate_with_deepseek_v2(self, prompt, max_tokens=None):
        """
        Generates code using the Deepseek-V2 model via Ollama.
        """
        if not self.deepseek_v2_available:
            raise RuntimeError("Deepseek-V2 model is not available on Ollama.")

        payload = {
            "model": self.deepseek_v2_model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": 16384,
                "num_predict": max_tokens or 4096
            }
        }
        
        try:
            logger.info(f"Attempting to generate with Ollama using POST {self.ollama_api_url}")
            response = requests.post(self.ollama_api_url, json=payload, timeout=300)
            response.raise_for_status()
            
            # Ollama returns a JSON string in the 'response' field
            response_data = response.json()
            generated_text = response_data.get('response', '')

            # The API response structure for generate is just the JSON object
            # but let's structure it like the OpenAI API for consistency
            return {"choices": [{"text": generated_text}]}

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}. Is Ollama running?")
            raise RuntimeError(f"Ollama connection failed: {e}")
        except requests.exceptions.Timeout:
            logger.error("Request to Ollama timed out.")
            raise RuntimeError("Ollama request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found. Check if Ollama is running and the model '{self.deepseek_v2_model_name}' is available.")
                raise RuntimeError(f"Ollama API not found (404). Is Ollama running with the correct model?")
            else:
                logger.error(f"HTTP error from Ollama: {e}")
                raise RuntimeError(f"Ollama HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred with the Ollama request: {e}")
            raise RuntimeError(f"Ollama request failed: {e}")

    def initialize_deepseek_6b_model(self, model_path, use_gpu=True):
        """Initializes the local 6.7B parameter model using llama-cpp-python."""
        if not Llama:
            msg = "llama-cpp-python is not installed. Please install it with GPU support if needed: pip install llama-cpp-python[server]"
            logger.error(msg)
            return False, msg

        try:
            n_gpu_layers = -1 if use_gpu else 0
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_gpu_layers=n_gpu_layers,
                verbose=True,
                n_threads=psutil.cpu_count(logical=False) # Use physical cores
            )
            self.deepseek_6b_initialized = True
            msg = f"Successfully initialized local model from {model_path} with use_gpu={use_gpu}"
            logger.info(msg)
            return True, msg
        except Exception as e:
            self.deepseek_6b_initialized = False
            msg = f"Failed to load local model: {e}"
            logger.error(msg)
            return False, msg

    def _extract_methods_with_details(self, java_code):
        """
        Extracts public method signatures with details (name, return type, parameters).
        """
        methods = []
        # Regex to capture public methods, their return types, names, and parameters
        # This is a bit more robust and handles generics in return types.
        method_pattern = re.compile(
            r'public\s+(?:static\s+|final\s+)?([\w<>,.?\s\[\]]+)\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*(?:throws\s+[\w,.\s]+)?\s*{',
            re.MULTILINE
        )
        
        for match in method_pattern.finditer(java_code):
            return_type = match.group(1).strip()
            method_name = match.group(2).strip()
            params_str = match.group(3).strip()
            
            # Simple check to exclude constructors
            if method_name == self._extract_class_name(java_code):
                continue

            params = []
            if params_str:
                # Split parameters, trying to be mindful of generics
                # This is a simplification and might not handle all edge cases
                raw_params = params_str.split(',')
                for param in raw_params:
                    param = param.strip()
                    # Find the last space to separate type and name
                    last_space_idx = param.rfind(' ')
                    if last_space_idx != -1:
                        param_type = param[:last_space_idx].strip()
                        param_name = param[last_space_idx:].strip()
                        params.append({'type': param_type, 'name': param_name})

            methods.append({
                'name': method_name,
                'return_type': return_type,
                'parameters': params
            })
        
        return methods

    def _extract_static_method_calls(self, java_code):
        """Extracts static method calls (e.g., ClassName.methodName(...)) from the code."""
        # This regex looks for patterns like `Word.word(` and assumes it's a static call.
        # It's a heuristic and might have false positives (e.g., `object.method()`).
        # A more robust solution would involve a proper Java parser.
        static_call_pattern = re.compile(r'\b([A-Z]\w*)\.([a-z]\w*)\s*\(')
        matches = static_call_pattern.findall(java_code)
        
        # We only want unique calls, like "ClassName.methodName"
        unique_calls = sorted(list(set([f"{class_name}.{method_name}" for class_name, method_name in matches])))
        
        return unique_calls

    def _extract_package_name(self, java_code):
        """Extracts the package name from Java code."""
        package_match = re.search(r'package\s+([\w.]+);', java_code)
        if package_match:
            return package_match.group(1)
        return ""

    def _remove_comments(self, java_code):
        """Removes comments from Java code to reduce token count."""
        # Remove block comments
        code = re.sub(r'/\*.*?\*/', '', java_code, flags=re.DOTALL)
        # Remove line comments
        code = re.sub(r'//.*', '', code)
        return code

    def _get_class_context(self, java_code, methods_with_details):
        """Returns the class definition without method bodies for context."""
        class_body_without_methods = self._remove_comments(java_code)
        
        # Iteratively remove method bodies
        for method in methods_with_details:
             # Build a regex to find the specific method signature and its body
            method_name = method['name']
            # This is tricky without a full parser. We'll find the method signature
            # and then find the opening brace and its matching closing brace.
            # This is a simplification and might fail on complex code.
            
            # Let's try a simpler approach: just remove content between the first and last brace
            try:
                start_brace = class_body_without_methods.index('{', class_body_without_methods.find(f"{method['return_type']} {method_name}"))
                # This is still too naive. For now, let's just return the code with comments removed.
            except ValueError:
                continue

        return class_body_without_methods


    def _get_class_type(self, java_code):
        """Determines if the class is a Service, Controller, Repository, or Component."""
        if re.search(r'@(Service|Service\s*\()', java_code):
            return "Service"
        if re.search(r'@(RestController|Controller)', java_code):
            return "Controller"
        if re.search(r'@(Repository|Repository\s*\()', java_code):
            return "Repository"
        if re.search(r'@(Component|Component\s*\()', java_code):
            return "Component"
        return "Class"

    def generate_junit_tests(self, java_code, class_name=None, model_type="auto"):
        """
        Main method to generate JUnit tests for a given Java class.
        It orchestrates the process of parsing, chunking, and generating tests.
        """
        if not class_name:
            class_name = self._extract_class_name(java_code)
            if not class_name:
                return self._generate_fallback_demo_class("UnknownClass")

        package_name = self._extract_package_name(java_code)
        
        # Decide which generation strategy to use
        # If the code is small, single-shot is faster.
        # Let's define "small" as under 200 lines.
        if len(java_code.split('\n')) < 200:
             logger.info("Code is small, using single-shot generation.")
             return self._generate_tests_single_shot(java_code, class_name, package_name, model_type)
        else:
             logger.info("Code is large, using chunked generation.")
             return self._generate_tests_chunked(java_code, class_name, package_name, model_type)

    def _generate_tests_single_shot(self, java_code, class_name, package_name, model_type):
        """
        Generates a complete test class in a single request to the AI model.
        Suitable for smaller classes.
        """
        dependencies = self._extract_dependencies(java_code)
        value_fields = self._extract_value_fields(java_code)
        methods = self._extract_methods_with_details(java_code)
        
        dependencies_declarations = self._format_dependencies_for_prompt(dependencies)
        
        prompt = f"""You are a world-class Java test engineer. Generate a complete JUnit 5 test class for the following Java class.

### Java Class to Test
```java
{java_code}
```

### CRITICAL REQUIREMENTS
1.  **Full Class:** Generate a complete, runnable JUnit 5 test class, including package, imports, class declaration, fields, and test methods.
2.  **Structure:**
    - Use `@ExtendWith(MockitoExtension.class)`.
    - Use `@Mock` for all dependencies: {', '.join([d['name'] for d in dependencies])}.
    - Use `@InjectMocks` for the class under test: `{class_name.lower()}`.
    - If applicable, include a `@BeforeEach` `setUp()` method for common test arrangements.
3.  **Test Naming:** Use the `test<MethodName>_<Scenario>` convention.
4.  **Coverage:**
    - For each public method in `{class_name}`, create at least one success and one failure/exception test case.
    - Use `assertThrows` to verify expected exceptions.
    - Mock dependencies to return values for success cases (`when(...).thenReturn(...)`) and to throw exceptions for failure cases (`when(...).thenThrow(...)`).
5.  **Quality:**
    - Follow the **Arrange-Act-Assert** pattern, with comments.
    - Use meaningful assertions (`assertEquals`, `assertNotNull`, `assertTrue`, etc.).
    - Verify mock interactions using `verify()`.
    - DO NOT include `// TODO` or placeholder comments.

### Example Test Method Structure:
```java
@Test
public void testSomeMethod_Success() {{
    // Arrange
    when(dependency.someCall(anyString())).thenReturn("mocked response");

    // Act
    String result = {class_name.lower()}.someMethod("input");

    // Assert
    assertNotNull(result);
    assertEquals("expected outcome", result);
    verify(dependency, times(1)).someCall(anyString());
}}
```

Provide the complete Java test class file.
"""
        
        try:
            if model_type == '6b' and self.deepseek_6b_initialized:
                 # Local model generation (not implemented in this snippet)
                 raise NotImplementedError("Local 6.7B model generation is not fully implemented here.")
            else:
                 response = self.generate_with_deepseek_v2(prompt, max_tokens=4000)
                 generated_text = response['choices'][0]['text']

            # Clean the generated code
            return self._clean_generated_code(generated_text, class_name)
                
        except Exception as e:
            logger.error(f"Single-shot test generation failed: {e}")
            return self._generate_fallback_demo_class(class_name, package_name)

    def _generate_tests_chunked(self, java_code, class_name, package_name, model_type="auto"):
        """
        Generates tests by splitting the source code into chunks and generating tests for each chunk.
        This is more reliable for large classes.
        """
        all_methods_details = self._extract_methods_with_details(java_code)
        if not all_methods_details:
            logger.warning("No methods found to test.")
            return self._generate_fallback_demo_class(class_name, package_name)

        dependencies = self._extract_dependencies(java_code)
        value_fields = self._extract_value_fields(java_code)
        dependencies_declarations = self._format_dependencies_for_prompt(dependencies)
        class_type = self._get_class_type(java_code)
        static_calls = self._extract_static_method_calls(java_code)

        chunks = self._split_code_into_chunks(java_code)
        all_test_methods = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Find which methods are in the current chunk
            methods_in_chunk = [
                method for method in all_methods_details 
                if method['name'] in chunk
            ]
            if not methods_in_chunk:
                continue

            # Generate tests for this chunk
            chunk_test_methods = self._generate_tests_for_chunk(
                chunk, methods_in_chunk, class_name, dependencies_declarations, 
                class_type, value_fields, static_calls
            )
            all_test_methods.extend(chunk_test_methods)
            
        if not all_test_methods:
            logger.error("No test methods were generated after processing all chunks.")
            # Fallback to generating a demo class based on all found methods
            return self._generate_demo_tests(java_code, class_name)

        # Merge all generated test methods into a final class file
        return self._merge_test_methods_into_class(all_test_methods, class_name, dependencies, value_fields, package_name)

    def _split_code_into_chunks_legacy(self, java_code, lines_per_chunk=100):
        """A simple legacy method to split code by line count."""
        lines = java_code.split('\n')
        chunks = []
        for i in range(0, len(lines), lines_per_chunk):
            chunks.append('\n'.join(lines[i:i + lines_per_chunk]))
        return chunks

    def _split_code_into_chunks(self, java_code, lines_per_chunk=100):
        """
        Splits Java code into logical chunks, keeping methods intact.
        Also includes relevant class-level fields in each chunk.
        """
        lines = java_code.split('\n')
        
        # Extract class-level content (imports, fields, constructor)
        class_header = []
        body_lines = []
        in_class_body = False
        brace_level = 0
        
        for line in lines:
            if '{' in line:
                if not in_class_body:
                    in_class_body = True
                brace_level += line.count('{')
            
            if '}' in line:
                brace_level -= line.count('}')

            if in_class_body:
                body_lines.append(line)
            else:
                class_header.append(line)
        
        # Simplified: for now, we'll just split by methods.
        # A more advanced version would handle chunks of multiple methods.
        
        methods_with_details = self._extract_methods_with_details(java_code)
        class_context = self._get_class_context(java_code, methods_with_details)
        
        chunks = []
        # Create a chunk for each method
        for method in methods_with_details:
            # This is still not right. We need the method body.
            # A simple regex to find the method body is brittle.
            # Let's revert to a simpler chunking for now, but method-aware.
            pass

        # Let's find method boundaries and split based on them.
        method_starts = [java_code.find(f"public {m['return_type']} {m['name']}") for m in methods_with_details]
        method_starts = sorted([m for m in method_starts if m != -1])
        
        if not method_starts:
            return [java_code] # Return the whole thing as one chunk if no methods found

        chunks = []
        start = 0
        
        # The first chunk is everything before the first method
        # This includes imports, fields, constructors, which is good context.
        # We might not generate tests for it, but it's needed for context.
        first_method_start = method_starts[0]
        # Let's redefine the first chunk to be everything up to the end of the first method
        # This is getting too complex without a parser.
        
        # New strategy: A chunk is a method.
        method_bodies = self._extract_method_bodies(java_code)
        for method_name, method_body in method_bodies.items():
            # Add class context to each method
            chunk = class_context + "\n\n" + method_body
            chunks.append(chunk)

        if not chunks:
            return [java_code]

        return chunks

    def _extract_method_bodies(self, java_code):
        """
        A helper to extract full method bodies. Very heuristic.
        Returns a dict of method_name: full_method_text.
        """
        method_bodies = {}
        methods_details = self._extract_methods_with_details(java_code)
        
        for method in methods_details:
            try:
                # Find the start of the method signature
                # This is still not perfect due to overloading.
                method_signature_start = java_code.find(f"{method['return_type']} {method['name']}")
                if method_signature_start == -1: continue

                # From there, find the first '{'
                first_brace = java_code.index('{', method_signature_start)
                
                # Scan for the matching '}'
                brace_level = 1
                current_pos = first_brace + 1
                while current_pos < len(java_code) and brace_level > 0:
                    if java_code[current_pos] == '{': brace_level += 1
                    if java_code[current_pos] == '}': brace_level -= 1
                    current_pos += 1
                
                # We found the method body
                method_text = java_code[method_signature_start:current_pos]
                # Let's also add the public keyword back
                full_method_text = "public " + method_text
                method_bodies[method['name']] = full_method_text

            except ValueError:
                continue
        
        return method_bodies


    def _format_dependencies_for_prompt(self, dependencies):
        """Formats the list of dependencies for inclusion in the prompt."""
        if not dependencies:
            return "None"
        
        declarations = []
        for dep in dependencies:
            # Get the simple class name
            simple_type = dep['type'].split('.')[-1]
            declarations.append(f"{simple_type} {dep['name']}")
            
        return "\n".join([f"- {d}" for d in declarations])

    def _generate_prompt_for_class_type(self, class_type):
        """Generates specific instructions based on the class stereotype."""
        if class_type == "Controller":
            return "For Controller classes, focus on testing API endpoints. Mock service layer calls and verify HTTP status codes and response bodies. Use MockMvc if applicable."
        if class_type == "Service":
            return "For Service classes, test the business logic. Mock repository or other service calls. Verify the interactions and the data returned."
        if class_type == "Repository":
            return "For Repository classes, tests are often integration tests. For unit tests, you might be testing custom query methods. If using Spring Data, mock the repository interface."
        return ""

    def _generate_setup_prompt(self, value_fields, class_name, has_object_mapper):
        """
        Generates a prompt to create the @BeforeEach setup method.
        """
        instructions = [
            "Create a `@BeforeEach` setup method.",
            f"`{class_name.lower()} = new {class_name}(...);` should be initialized here if using constructor injection.",
            "If `RestTemplate` is a dependency, consider setting up a `MockRestServiceServer`."
        ]
        
        if value_fields:
            instructions.append("Use `ReflectionTestUtils.setField(...)` to inject mocked values for @Value fields.")
        
        if has_object_mapper:
            instructions.append("Initialize the ObjectMapper: `objectMapper = new ObjectMapper();` and inject it if needed.")
            
        instruction_str = "\n- ".join(instructions)
        prompt = f"""Based on the following class context, generate the `@BeforeEach` setup block for the JUnit 5 test class.

**Context:**
- Class under test: `{class_name}`
- @Value fields: {', '.join([f[0] for f in value_fields]) if value_fields else 'None'}
- ObjectMapper present: {has_object_mapper}

**Instructions:**
- {instruction_str}

**Output only the `@BeforeEach` method code.**
"""
        return prompt

    def _generate_tests_for_chunk(self, chunk, methods_in_chunk, class_name, dependencies_declarations, class_type, value_fields, static_calls):
        """Generate test methods for a chunk of code with improved URL handling"""
        
        # Build a map of @Value field names for better test generation
        value_field_names = [field[0] for field in value_fields] if value_fields else []
        has_server_url = 'serverUrl' in value_field_names
        
        # Prepare the URL construction instruction
        url_instruction = "Use 'serverUrl + \"/endpoint\"' for URL construction since serverUrl is injected via @Value" if has_server_url else "Use complete hardcoded URLs"
        
        # Build the prompt using safe string concatenation to avoid f-string parsing issues.
        prompt_parts = [
            "You are a world-class expert Java test engineer specializing in creating comprehensive JUnit 5 tests.\n",
            "Your task is to generate test methods for a given chunk of Java code.\n\n",

            "### CONTEXT\n",
            f"- **Class Under Test:** {class_name}\n",
            f"- **Dependencies Available for Mocking:** {dependencies_declarations}\n",
            f"- **@Value Fields Available:** {', '.join(value_field_names) if value_field_names else 'None'}\n",
            f"- **Static method calls detected:** {', '.join(static_calls) if static_calls else 'None'}\n",
            f"- **Methods to test in this chunk:** {[m['name'] for m in methods_in_chunk]}\n\n",

            "### CODE CHUNK TO TEST\n",
            f"```java\n{chunk}\n```\n\n",

            "### CRITICAL REQUIREMENTS FOR TEST GENERATION\n",
            "1.  **Frameworks:** Use **JUnit 5** (`@Test`, `@BeforeEach`, `assertThrows`, etc.) and **Mockito** (`when`, `verify`, `any`, `ArgumentCaptor`).\n",
            "2.  **Test Naming Convention:** Test methods MUST follow the pattern `test<MethodName>_<Scenario>[_Success | _Failure | _ThrowsException]`.\n",
            "    - Example: `testProcessLoanDocuments_Success`, `testStoreDocuments_WithInvalidResponse`, `testGetPartnerBankAccount_WhenPartnerNotFound_ThrowsResourceNotFoundException`.\n",
            "3.  **Structure (Arrange-Act-Assert):** Every test method MUST be clearly structured with comments:\n",
            "    ```java\n",
            "    // Arrange\n",
            "    // ... setup data and mock behavior ...\n\n",
            "    // Act\n",
            "    // ... call the method under test ...\n\n",
            "    // Assert\n",
            "    // ... assert outcomes and verify mock interactions ...\n",
            "    ```\n",
            "4.  **Test Coverage:**\n",
            "    - **Success Scenarios:** Create at least one test for the primary success path.\n",
            "    - **Failure Scenarios:** Create tests for expected failures, such as invalid input, empty lists, or null arguments.\n",
            "    - **Exception Handling:** If a method can throw an exception (e.g., `BusinessException`, `ResourceNotFoundException`), create a test case that verifies the exception is thrown using `assertThrows`. Mock dependencies to throw exceptions (`when(...).thenThrow(...)`).\n",
            "    - **Edge Cases:** Test for edge cases like empty collections, null values, zero values, etc.\n",
            "5.  **Mocking and Verification:**\n",
            "    - **Mocking:** Use `when(mockObject.method(any...)).thenReturn(response)` to define mock behavior. For complex objects, use builders (`YourDTO.builder()...build()`) to construct return values.\n",
            "    - **Verification:** Use `verify(mockObject, times(1)).method(...)` to check that methods were called. Use `verify(mockObject, never()).method(...)` for methods that should not be called.\n",
            "6.  **Code Quality:**\n",
            "    - **No Placeholders:** Generate complete, runnable code. DO NOT use comments like `// TODO`.\n",
            "    - **Constants:** For recurring values like IDs or strings, consider defining them as `private static final` constants if they were part of the full class context (for this chunk, inline is fine).\n",
            f"    - **URL Construction:** {url_instruction}\n",
            "    - **Generics:** Be explicit with generic types in mock return values. For example, use `new ServiceResponse<MyDTO>()` instead of `new ServiceResponse<>()`.\n\n",

            "### OUTPUT FORMAT\n",
            "Generate **ONLY** the Java code for the `@Test` methods. Do **NOT** include the class declaration, fields, or `@BeforeEach` method. Start directly with the first `@Test` annotation.\n"
        ]
        prompt = "".join(prompt_parts)
        
        logger.info(f"Generating tests for {len(methods_in_chunk)} methods: {[m['name'] for m in methods_in_chunk]}")
        
        try:
            if self.deepseek_v2_available:
                response = self.generate_with_deepseek_v2(prompt, max_tokens=3000)
                generated_text = response['choices'][0]['text']
            else:
                # If the primary model isn't available, use fallback
                logger.warning("Deepseek-V2 model is not available, generating demo test methods")
                return self._generate_demo_test_methods(methods_in_chunk, class_name)
            
            # Extract and clean test methods
            test_methods = self._extract_test_methods_from_response(generated_text)
            
            # Improve URL handling in test methods
            improved_methods = []
            for method in test_methods:
                if has_server_url and 'restTemplate' in method:
                    # Replace hardcoded URLs with serverUrl + endpoint pattern
                    method = re.sub(
                        r'"http://[^"]*/([\w\-]+)"', 
                        r'serverUrl + "/\1"', 
                        method
                    )
                    # Fix common URL construction issues
                    method = method.replace('serverUrl + "/', 'serverUrl + "/')
                improved_methods.append(method)
            
            return improved_methods
            
        except Exception as e:
            # Generate demo test methods as fallback instead of failing completely
            logger.error(f"AI generation failed for chunk: {str(e)}")
            logger.info("Generating demo test methods as fallback...")
            return self._generate_demo_test_methods(methods_in_chunk, class_name)

    def _generate_demo_test_methods(self, methods_in_chunk, class_name):
        """Generate basic demo test methods when AI generation fails"""
        demo_methods = []
        
        for method in methods_in_chunk:
            method_name = method['name']
            return_type = method.get('return_type', 'void')
            
            if return_type == 'boolean':
                demo_methods.append(f"""    @Test
    public void test{method_name.capitalize()}_Success() {{{{
        // Arrange
        // TODO: Setup test data and mocks
        
        // Act
        boolean result = {class_name.lower()}.{method_name}();
        
        // Assert
        assertTrue(result);
    }}}}
    
    @Test
    public void test{method_name.capitalize()}_Failure() {{{{
        // Arrange
        // TODO: Setup failure scenario
        
        // Act
        boolean result = {class_name.lower()}.{method_name}();
        
        // Assert
        assertFalse(result);
    }}}}""")
            else:
                demo_methods.append(f"""    @Test
    public void test{method_name.capitalize()}_Success() {{{{
        // Arrange
        // TODO: Setup test data and mocks
        
        // Act
        {return_type} result = {class_name.lower()}.{method_name}();
        
        // Assert
        assertNotNull(result);
    }}}}""")
        
        return demo_methods

    def _extract_test_methods_from_response(self, response_text):
        """Extracts and cleans individual @Test methods from the AI's response"""
        
        # Normalize line endings
        response_text = response_text.replace('\r\n', '\n')
        
        # Remove markdown code block fences
        response_text = re.sub(r'```java\n?', '', response_text)
        response_text = re.sub(r'```', '', response_text)

        # Pattern to find methods starting with @Test
        test_method_pattern = r'(@Test.*?^(?=\s*@Test|\Z))'
        
        # Find all test methods
        test_methods = re.findall(test_method_pattern, response_text, re.DOTALL | re.MULTILINE)
        
        # Clean up each method
        cleaned_methods = []
        for method in test_methods:
            # Trim whitespace and ensure it's a valid method
            method = method.strip()
            if method.endswith('}') and 'public void' in method:
                cleaned_methods.append(method)

        # Fallback for when the regex doesn't find methods but there's code
        if not cleaned_methods and response_text.strip().startswith('@Test'):
            # Attempt to split by @Test and reconstruct
            potential_methods = response_text.split('@Test')
            for potential_method in potential_methods:
                if 'public void' in potential_method:
                    method_text = '@Test\n' + potential_method.strip()
                    if method_text.count('{') == method_text.count('}'):
                        cleaned_methods.append(method_text)
        
        # If still no methods, try a simpler split
        if not cleaned_methods and "public void test" in response_text:
             # Look for the start of the first test
            start_index = response_text.find("@Test")
            if start_index != -1:
                # Assume the rest of the text is the method block
                method_block = response_text[start_index:].strip()
                # A simple validation
                if method_block.count('{') == method_block.count('}'):
                    cleaned_methods.append(method_block)
        
        logger.info(f"Extracted {len(cleaned_methods)} test methods.")
        return cleaned_methods

    def _extract_method_name(self, method_text):
        """Extracts method name from a test method string"""
        match = re.search(r'void\s+(test\w+)\s*\(', method_text)
        if match:
            return match.group(1)
        return None

    def _is_test_method_complete(self, method_text):
        """
        Check if a generated test method is complete.
        A complete method should not have placeholder comments.
        """
        placeholder_comments = [
            "// TODO",
            "// Add assertions here",
            "// Implement test logic",
            "// Arrange",
            "// Act",
            "// Assert"
        ]
        
        # Check for exact placeholder comments
        if any(comment in method_text for comment in placeholder_comments):
            # Further check if there's any actual code in the blocks
            if "// Arrange" in method_text and "// Act" in method_text:
                arrange_block = method_text.split("// Arrange")[1].split("// Act")[0].strip()
                if not arrange_block: return False
            
            if "// Act" in method_text and "// Assert" in method_text:
                act_block = method_text.split("// Act")[1].split("// Assert")[0].strip()
                if not act_block: return False
                
            if "// Assert" in method_text:
                assert_block = method_text.split("// Assert")[1].strip()
                # Remove closing brace for check
                if assert_block.endswith('}'):
                    assert_block = assert_block[:-1].strip()
                if not assert_block: return False

        # Check for balanced braces
        if method_text.count('{') != method_text.count('}'):
            return False
            
        return True

    def _fix_incomplete_test_method(self, method_text):
        """
        Uses the AI to fix an incomplete test method.
        This can be expanded to be more sophisticated.
        """
        class_name = self._extract_class_name(method_text) or "UnknownClass"
        method_name = self._extract_method_name(method_text) or "unknownMethod"

        prompt = f"""The following JUnit test method is incomplete. It may be missing setup, assertions, or contain placeholder comments. 
Please complete the test method based on the context. Make it a complete, runnable test.

**Incomplete Test Method:**
```java
{method_text}
```

**CRITICAL INSTRUCTIONS:**
1. Replace all `// TODO` or placeholder comments with real, working Java code.
2. Ensure the "Arrange" block has proper mock setup (e.g., `when(...).thenReturn(...)`).
3. Ensure the "Act" block calls the method under test.
4. Ensure the "Assert" block has meaningful assertions (e.g., `assertEquals`, `assertNotNull`, `assertTrue`) and `verify` calls.
5. Return ONLY the complete, corrected Java code for the method. Do not include extra explanations.

**Completed Test Method:**
"""
        
        try:
            response = self.generate_with_deepseek_v2(prompt, max_tokens=1000)
            fixed_code = response['choices'][0]['text']
            # Clean up the response
            fixed_code = fixed_code.strip()
            if fixed_code.startswith("```java"):
                fixed_code = fixed_code[7:]
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-3]
            
            return fixed_code.strip()
        except Exception as e:
            logger.error(f"Error fixing incomplete test method: {e}")
            return method_text # Return original on failure

    def _merge_test_methods_into_class(self, all_test_methods, class_name, dependencies, value_fields, package_name):
        """
        Merges a list of generated @Test methods into a complete JUnit 5 test class file.
        """
        
        # --- Imports ---
        imports = {
            "org.junit.jupiter.api.Test",
            "org.junit.jupiter.api.extension.ExtendWith",
            "org.mockito.InjectMocks",
            "org.mockito.Mock",
            "org.mockito.junit.jupiter.MockitoExtension"
        }
        
        # Basic assertions
        imports.add("static org.junit.jupiter.api.Assertions.*")
        
        # Mockito static imports
        imports.add("static org.mockito.Mockito.*")
        imports.add("static org.mockito.ArgumentMatchers.*")
        
        # Add imports based on dependencies
        for dep in dependencies:
            if dep['type'] and '.' in dep['type']:
                imports.add(dep['type'])
        
        # Add imports from method bodies
        full_method_text = "\n".join(all_test_methods)
        
        # Find all capitalized words that could be classes (heuristic)
        potential_classes = re.findall(r'\b[A-Z][\w\.]*\b', full_method_text)
        
        # Common Java standard library imports
        if "List" in potential_classes: imports.add("java.util.List")
        if "Map" in potential_classes: imports.add("java.util.Map")
        if "Optional" in potential_classes: imports.add("java.util.Optional")
        if "Collections" in potential_classes: imports.add("java.util.Collections")
        if "ArrayList" in potential_classes: imports.add("java.util.ArrayList")
        if "HashMap" in potential_classes: imports.add("java.util.HashMap")
        
        # Add imports for custom DTOs/Entities - This is a heuristic
        # We assume they are in a package relative to the current package
        for pc in potential_classes:
            if pc.endswith("DTO") or pc.endswith("Entity") or pc.endswith("Request") or pc.endswith("Response"):
                # This is a guess, might need to be smarter
                base_package = ".".join(package_name.split('.')[:-2])
                if ".model." in full_method_text:
                    imports.add(f"{base_package}.model.{pc}")
                elif ".dto." in full_method_text:
                    imports.add(f"{base_package}.dto.{pc}")
                elif ".entity." in full_method_text:
                    imports.add(f"{base_package}.entity.{pc}")

        
        sorted_imports = sorted(list(imports))
        import_statements = "\n".join([f"import {i};" for i in sorted_imports])
        
        # --- Fields ---
        dependency_fields = "\n".join([f"    @Mock\n    private {dep['type'].split('.')[-1]} {dep['name']};" for dep in dependencies])
        value_field_declarations = "\n".join([f'    @Value("${{{field[1]}}}")\n    private {field[2]} {field[0]};' for field in value_fields])

        # --- Test Class Structure ---
        test_class_template = f"""package {package_name};

{import_statements}

@ExtendWith(MockitoExtension.class)
class {class_name}Test {{

    @InjectMocks
    private {class_name} {class_name.lower()};

{dependency_fields}

{value_field_declarations}

    // You can add a @BeforeEach method here for common setup if needed

{chr(10).join(all_test_methods)}
}}
"""
        
        return test_class_template

    def _extract_test_methods_from_class(self, java_code):
        """Extracts methods from a full Java class file for iterative regeneration."""
        test_method_pattern = r'(@Test.*?}\s*})'
        return re.findall(test_method_pattern, java_code, re.DOTALL)

    def _validate_generated_code(self, code, class_name):
        """
        Validates the generated Java code for basic correctness.
        Returns a list of error messages.
        """
        errors = []
        
        # 1. Check for balanced braces
        if code.count('{') != code.count('}'):
            errors.append(f"Mismatched curly braces {{}}: {code.count('{')} opening vs {code.count('}')} closing.")
        
        # 2. Check for placeholder comments
        if "// TODO" in code:
            errors.append("Generated code contains placeholder '// TODO' comments.")
        
        # 3. Check for compilation (basic syntax check) - requires a temporary file
        # This is more complex and may be added later. For now, we rely on syntax hints.
        
        # 4. Check for missing @Test annotations
        public_void_methods = len(re.findall(r'public void test', code))
        test_annotations = code.count('@Test')
        if public_void_methods > test_annotations:
            errors.append(f"Found {public_void_methods} test methods but only {test_annotations} @Test annotations.")
            
        return errors
        
    def _generate_demo_tests(self, java_code, class_name):
        """
        Generates a very basic, non-AI-powered demo test class.
        This serves as a fallback if the AI fails completely.
        """
        package_name = self._extract_package_name(java_code)
        methods = self._extract_methods(java_code)
        
        test_methods = []
        for method in methods:
            method_name_cap = method.capitalize()
            test_methods.append(f"""
    @Test
    void test{method_name_cap}_RunsWithoutErrors() {{
        // This is a basic test to ensure the method can be called without runtime errors.
        // It does not validate the output.
        // TODO: Implement a proper test for this method.
        
        // Arrange
        // Mock dependencies for {class_name.lower()} here.
        
        try {{
            // Act
            {class_name.lower()}.{method}();
            
            // Assert
            // Add assertions here to validate the results.
            
        }} catch (Exception e) {{
            fail("The method '{method}' threw an unexpected exception: " + e.getMessage());
        }}
    }}
""")
        
        test_methods_str = "\n".join(test_methods)
        
        demo_class = f"""package {package_name};

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.fail;

// TODO: This is a basic, AI-generated test class.
// You need to mock the dependencies and add proper assertions.

@ExtendWith(MockitoExtension.class)
class {class_name}Test {{

    @InjectMocks
    private {class_name} {class_name.lower()};
    
    // TODO: Add @Mock annotations for all dependencies of {class_name}
    // Example:
    // @Mock
    // private SomeService someService;

{test_methods_str}
}}
"""
        return demo_class

    # --- Utility Methods ---

    def _extract_class_name(self, java_code):
        """Extracts the primary public class name from Java code."""
        class_name_match = re.search(r'public\s+class\s+([\w]+)', java_code)
        if class_name_match:
            return class_name_match.group(1)
        
        # Fallback for interface or abstract class
        interface_name_match = re.search(r'public\s+(interface|abstract class)\s+([\w]+)', java_code)
        if interface_name_match:
            return interface_name_match.group(2)
            
        return None

    def _extract_methods(self, java_code):
        """Extracts public method names from Java code."""
        # This regex looks for public methods, excluding constructors
        method_pattern = re.compile(r'public\s+(?!class|interface|enum|static\s+final)\s+[\w<>,?]+\s+([a-zA-Z]\w*)\s*\(')
        methods = method_pattern.findall(java_code)
        return methods

    def _clean_generated_code(self, generated_text, class_name):
        """
        Cleans the raw output from the AI model to produce a valid Java class file.
        """
        # Remove markdown fences
        cleaned_text = re.sub(r'```java\n?', '', generated_text)
        cleaned_text = re.sub(r'```', '', cleaned_text)
        
        # Find the package declaration
        package_match = re.search(r'package\s+[\w.]+;', cleaned_text)
        if not package_match:
            # If no package, something is wrong, return a basic error structure
            return f"// AI Generation Error: Could not find package declaration.\n{cleaned_text}"
            
        package_decl = package_match.group(0)
        
        # Find the class declaration
        class_decl_match = re.search(r'@ExtendWith\(MockitoExtension\.class\)\s+class\s+' + class_name + r'Test\s*\{', cleaned_text, re.DOTALL)
        if not class_decl_match:
            return f"// AI Generation Error: Could not find class declaration for {class_name}Test.\n{cleaned_text}"
            
        class_start_index = class_decl_match.start()
        
        # Extract imports (everything between package and class declaration)
        imports_section = cleaned_text[len(package_decl):class_start_index].strip()
        
        # Extract the class body
        class_body_start = class_decl_match.end()
        # Find the corresponding closing brace for the class
        open_braces = 1
        current_pos = class_body_start
        while open_braces > 0 and current_pos < len(cleaned_text):
            if cleaned_text[current_pos] == '{':
                open_braces += 1
            elif cleaned_text[current_pos] == '}':
                open_braces -= 1
            current_pos += 1
            
        class_body = cleaned_text[class_body_start:current_pos-1].strip()
        
        # Reconstruct the class cleanly
        final_code = f"{package_decl}\n\n{imports_section}\n\n{class_decl_match.group(0)}\n\n{class_body}\n}}\n"
        
        return final_code

    def check_ollama_running(self):
        """Check if Ollama service is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_system_info(self):
        """Returns a dictionary with system information."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

    def _extract_dependencies(self, java_code):
        """
        Extracts injected dependencies from Java code.
        Looks for fields annotated with @Autowired, @Inject, @Mock, etc.
        and constructor parameters.
        """
        dependencies = []
        
        # 1. Field Injection - More robust regex
        field_injection_pattern = re.compile(
            # Catches @Autowired, @Inject, @Resource, @Mock
            r'@(Autowired|Inject|Resource|Mock)\s+'
            # Handles optional access modifiers and keywords like static/final
            r'(?:private|public|protected)?\s*'
            r'(?:static\s+)?(?:final\s+)?'
            r'([\w.<>\[\]]+)\s+'  # Group 1: The dependency type (e.g., List<String>)
            r'(\w+);'             # Group 2: The dependency name
        )
        found_fields = field_injection_pattern.findall(java_code)
        # Unpack annotation, type, and name. We only need type and name.
        for _, dep_type, dep_name in found_fields:
            dependencies.append({'name': dep_name, 'type': dep_type})

        # 2. Constructor Injection
        class_name = self._extract_class_name(java_code)
        if class_name:
            # Regex to find the constructor, assuming it's public
            # This can be complex due to multiple constructors, annotations, etc.
            # A simplified regex for a single public constructor:
            constructor_pattern = re.compile(
                r'public\s+' + class_name + r'\s*\(([^)]*)\)', re.DOTALL
            )
            match = constructor_pattern.search(java_code)
            if match:
                params_str = match.group(1)
                # Split parameters, handling generics
                # This simple split by comma can fail with complex generics like Map<String, List<String>>
                # A more robust parser would be needed for that.
                param_pattern = re.compile(r'([\w.<>]+)\s+(\w+)')
                constructor_params = param_pattern.findall(params_str)
                for dep_type, dep_name in constructor_params:
                    # Avoid adding duplicates from field injection
                    if not any(d['name'] == dep_name for d in dependencies):
                         dependencies.append({'name': dep_name, 'type': dep_type.strip()})
        
        # Remove duplicates by name
        unique_dependencies = {dep['name']: dep for dep in dependencies}.values()
        
        return list(unique_dependencies)

    def _extract_value_fields(self, java_code):
        """Extracts fields annotated with @Value."""
        value_pattern = re.compile(
            r'@Value\s*\(\s*"\$\{([^}]+)\}"\s*\)\s*'
            # Handles optional access modifiers and keywords
            r'(?:private|public|protected)?\s*'
            r'(?:static\s+)?(?:final\s+)?'
            r'([\w.<>\[\]]+)\s+'  # Group 1: The field type
            r'(\w+);'             # Group 2: The field name
        )
        # The regex groups are: (key, type, name)
        # Example: ('serverUrl', 'server.url', 'String')
        found_values = value_pattern.findall(java_code)
        return [(name, key, dtype) for key, dtype, name in found_values]

    def _generate_fallback_demo_class(self, class_name, package_name=None):
        """Generates a fallback demo test class when all else fails."""
        package_decl = f"package {package_name};" if package_name else ""

        return f"""{package_decl}

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.fail;

/**
 * =================================================================
 *                          IMPORTANT
 * =================================================================
 * This is a fallback test class generated because the AI model
 * failed to produce a valid output.
 *
 * This class is NOT a valid JUnit test and WILL NOT COMPILE.
 *
 * PLEASE REVIEW THE LOGS FOR THE AI MODEL'S OUTPUT AND ERRORS.
 *
 * Common reasons for failure:
 * 1. The Java source file has syntax errors.
 * 2. The AI model produced incomplete or malformed code.
 * 3. A timeout occurred during generation.
 * =================================================================
 */
class {class_name}Test {{

    @Test
    void generationFailed() {{
        fail("AI test generation failed. Please see the comments in this file and check the application logs for more details.");
    }}
}}
"""


# --- Flask App ---
app = Flask(__name__)
generator = None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    if not generator:
        return jsonify({
            "status": "error",
            "message": "Generator not initialized"
        }), 503
    
    ollama_running = generator.check_ollama_running()
    
    return jsonify({
        "status": "ok" if ollama_running or generator.deepseek_6b_initialized else "degraded",
        "ollama": {
            "running": ollama_running,
            "url": generator.ollama_base_url,
            "deepseek_v2_available": generator.deepseek_v2_available
        },
        "fallback_model": {
            "deepseek_6b_initialized": generator.deepseek_6b_initialized
        },
        "system_info": generator.get_system_info()
    }), 200

@app.route('/models/status', methods=['GET'])
def models_status():
    """Check the status of the Deepseek models."""
    if not generator:
        return jsonify({"error": "Generator not initialized"}), 503
    
    status_v2 = generator.check_deepseek_v2_status()
    
    return jsonify({
        "deepseek_v2_ollama": status_v2,
        "deepseek_6b_local": {
            "initialized": generator.deepseek_6b_initialized,
            "model_path": generator.model_path if hasattr(generator, 'model_path') else "Not specified"
        }
    })

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initializes the fallback 6.7B model."""
    if not generator:
        return jsonify({"error": "Generator not initialized"}), 503
        
    data = request.json
    model_path = data.get('model_path')
    use_gpu = data.get('use_gpu', True)
    
    if not model_path:
        return jsonify({"error": "model_path is required"}), 400
        
    try:
        success, message = generator.initialize_deepseek_6b_model(model_path, use_gpu)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        logger.error(f"Failed to initialize 6.7B model: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/troubleshoot', methods=['GET'])
def troubleshoot():
    """Troubleshooting endpoint to diagnose Ollama connectivity issues."""
    if not generator:
        return jsonify({"error": "Generator not initialized"}), 503
    
    diagnostics = {
        "ollama_base_url": generator.ollama_base_url,
        "ollama_api_url": generator.ollama_api_url,
        "tests": {}
    }
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(f"{generator.ollama_base_url}/api/tags", timeout=5)
        diagnostics["tests"]["connectivity"] = {
            "status": "success",
            "response_code": response.status_code,
            "message": "Ollama is accessible"
        }
    except requests.exceptions.ConnectionError:
        diagnostics["tests"]["connectivity"] = {
            "status": "failed",
            "error": "Connection refused",
            "message": "Ollama is not running or not accessible"
        }
    except requests.exceptions.Timeout:
        diagnostics["tests"]["connectivity"] = {
            "status": "failed",
            "error": "Timeout",
            "message": "Ollama is running but not responding"
        }
    except Exception as e:
        diagnostics["tests"]["connectivity"] = {
            "status": "failed",
            "error": str(e),
            "message": "Unknown connectivity issue"
        }
    
    # Test 2: Model availability
    try:
        response = requests.get(f"{generator.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            deepseek_models = [name for name in model_names if 'deepseek' in name.lower()]
            
            diagnostics["tests"]["models"] = {
                "status": "success",
                "available_models": model_names,
                "deepseek_models": deepseek_models,
                "target_model": generator.deepseek_v2_model_name,
                "model_found": any(generator.deepseek_v2_model_name in name for name in model_names)
            }
        else:
            diagnostics["tests"]["models"] = {
                "status": "failed",
                "message": f"Got HTTP {response.status_code} when checking models"
            }
    except Exception as e:
        diagnostics["tests"]["models"] = {
            "status": "failed",
            "error": str(e),
            "message": "Could not check available models"
        }
    
    # Suggestions
    suggestions = []
    if diagnostics["tests"]["connectivity"]["status"] == "failed":
        suggestions.extend([
            "1. Check if Ollama is installed: `ollama --version`",
            "2. Start Ollama service: `ollama serve`",
            "3. Check if Ollama is running on the correct port (default: 11434)",
            "4. Verify firewall settings if running on different hosts"
        ])
    
    if diagnostics["tests"].get("models", {}).get("status") == "success":
        if not diagnostics["tests"]["models"].get("model_found", False):
            suggestions.extend([
                f"5. Pull the required model: `ollama pull {generator.deepseek_v2_model_name}`",
                "6. Check available models: `ollama list`"
            ])
    
    diagnostics["suggestions"] = suggestions
    
    return jsonify(diagnostics)

@app.route('/generate', methods=['POST'])
def generate():
    """Main endpoint to generate JUnit tests."""
    start_time = time.time()
    
    logger.info("--- Received request for /generate ---")
    logger.info(f"Request Headers: {request.headers}")
    
    if not generator:
        logger.error("Generator service not available at /generate endpoint.")
        return jsonify({"error": "Generator service not available"}), 503
        
    data = request.get_json(silent=True)
    if not data:
        logger.error(f"Malformed request: body is not valid JSON. Request body: {request.data}")
        return jsonify({"error": "Request must be a valid JSON"}), 400
    
    logger.info(f"Received JSON data: {data}")

    # Align with Java client which sends 'prompt' and 'className'
    java_code = data.get('prompt')
    class_name = data.get('className')
    # Align with Java client which sends 'model'
    model_type = data.get('model', 'auto')
        
    if not java_code:
        logger.error("Validation failed: 'prompt' key with java_code string is missing.")
        return jsonify({"error": "A 'prompt' string containing java_code is required"}), 400
    
    if not class_name:
        class_name = generator._extract_class_name(java_code)
        if not class_name:
            logger.error(f"Could not determine class name from the provided java_code.")
            return jsonify({"error": "Could not determine class name from java_code. Please provide it."}), 400
    
    try:
        logger.info(f"Generating tests for class: {class_name} with model: {model_type}")
        
        # Check if Ollama is available before proceeding
        if model_type != '6b' and not generator.check_ollama_running():
            logger.warning("Ollama is not running. Attempting to generate with fallback methods.")
            # Try to generate anyway, the fallback will kick in during chunk processing
        
        generated_tests = generator.generate_junit_tests(java_code, class_name, model_type)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check if we used fallback methods
        warnings = []
        if not generator.check_ollama_running():
            warnings.append("Generated using fallback methods due to Ollama unavailability")
        
        # Align response with what the Java client expects
        return jsonify({
            "response": generated_tests,
            "class_name": class_name,
            "generation_time_seconds": round(duration, 2),
            "model_used": model_type,
            "model_requested": data.get('model', 'auto'),
            "available_models": {
                "deepseek-v2": generator.deepseek_v2_available,
                "deepseek-6b": generator.deepseek_6b_initialized
            },
            "warnings": warnings
        })
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        
        # Provide more specific error messages
        if "Ollama" in str(e) or "404" in str(e):
            return jsonify({
                "error": "Ollama service is not available",
                "details": str(e),
                "troubleshooting": {
                    "check_health": "/health",
                    "troubleshoot": "/troubleshoot",
                    "suggestions": [
                        "Ensure Ollama is running: `ollama serve`",
                        f"Pull the required model: `ollama pull {generator.deepseek_v2_model_name}`",
                        "Check Ollama status: `ollama list`"
                    ]
                }
            }), 503
        else:
            return jsonify({"error": f"An internal error occurred: {e}"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

def main():
    global generator
    
    parser = argparse.ArgumentParser(description="JUnit Test Generator Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=9092, help="Port to run the server on.")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="URL of the Ollama server.")
    parser.add_argument("--deepseek-model", type=str, default="deepseek-coder-v2:16b", help="Name of the Deepseek model to use (e.g., deepseek-coder-v2:16b).")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level.")
    parser.add_argument("--use-gpu", action='store_true', help="Enable GPU for the local 6.7B model (if a path is provided later).")
    parser.add_argument("--model-path", type=str, default=None, help="Path to the local GGuf model file for the 6.7B fallback.")

    args = parser.parse_args()
    
    logging.basicConfig(level=args.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the generator
    generator = DeepSeekV2Generator(ollama_base_url=args.ollama_url, deepseek_model_name=args.deepseek_model)
    
    # Optionally initialize the 6.7B model at startup
    if args.model_path:
        logger.info(f"Initializing 6.7B model from path: {args.model_path}")
        generator.initialize_deepseek_6b_model(args.model_path, args.use_gpu)
    
    def signal_handler(sig, frame):
        logger.info('Shutting down server...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Starting server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()