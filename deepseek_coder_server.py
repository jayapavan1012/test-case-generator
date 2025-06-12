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

    def _create_chunk_generation_prompt(self, java_code, class_name, package_name, method_chunk):
        """Creates a prompt to generate tests for a small chunk of methods."""
        method_list = "\n".join([f"- `{m['return_type']} {m['name']}(...);`" for m in method_chunk])
        
        return f"""You are a Java test engineer. Your task is to write JUnit 5 test methods for a specific set of methods from a Java class.

### Full Class Context (for reference only)
```java
{java_code}
```

### INSTRUCTIONS
- Write complete, runnable JUnit 5 `@Test` methods for the following methods ONLY:
{method_list}
- For each method, provide at least one positive and one negative test case.
- Use the Arrange-Act-Assert pattern.
- Assume all necessary mocks (`@Mock`) and the class under test (`@InjectMocks private {class_name} {class_name[0].lower() + class_name[1:]};`) are already defined in the test class.
- DO NOT write the class definition, package statement, or imports.
- DO NOT write `@BeforeEach` or other setup methods.
- ONLY output the test methods themselves, without any surrounding markdown.

Generate the test methods now.
"""

    def _create_finalization_prompt(self, java_code, class_name, package_name, combined_snippets):
        """Creates a prompt to combine and finalize the generated test snippets."""
        dependencies = self._extract_dependencies(java_code)
        dep_list = ", ".join([f"`{d['type']} {d['name']}`" for d in dependencies]) or "None"

        return f"""You are a senior Java test automation engineer. Your task is to assemble a complete and valid JUnit 5 test class from a set of generated test method snippets.

### Original Java Class to Test
```java
package {package_name};

{java_code}
```

### Detected Dependencies to Mock
{dep_list}

### Generated Test Method Snippets
Here are the generated test methods. They may be incomplete, contain errors, or lack context.
```java
{combined_snippets}
```

### FINAL INSTRUCTIONS
1.  **Assemble a Single, Complete Class:** Create one full, runnable JUnit 5 test class named `{class_name}Test`.
2.  **Package and Imports:** Start with the correct package (`package {package_name};`) and add ALL necessary imports (JUnit, Mockito, etc.).
3.  **Class and Mock Setup:**
    - Annotate the class with `@ExtendWith(MockitoExtension.class)`.
    - Create `@Mock` fields for all dependencies.
    - Create the `@InjectMocks` field for the class under test.
    - Add a `@BeforeEach` `setUp()` method with `MockitoAnnotations.openMocks(this);`.
4.  **Integrate and Clean:**
    - Place all the provided test method snippets inside the class.
    - **Fix all syntax errors and consolidate duplicate imports.**
    - Ensure consistent formatting and that the code is complete.
5.  **No Placeholders:** The final output MUST be a complete, runnable file. Do not include `// TODO` or comments about missing code.

Generate the final, complete, and correct JUnit 5 test class now.
"""

    def _stitch_snippets_manually(self, java_code, class_name, package_name, combined_snippets):
        """A fallback method to stitch snippets together if the AI finalization fails."""
        logger.warning(f"AI finalization failed. Stitching snippets manually for {class_name}.")
        dependencies = self._extract_dependencies(java_code)
        
        imports = {
            "import org.junit.jupiter.api.Test;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "import static org.mockito.Mockito.*;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import org.junit.jupiter.api.extension.ExtendWith;",
            "import org.mockito.InjectMocks;",
            "import org.mockito.Mock;",
            "import org.mockito.MockitoAnnotations;",
            "import org.mockito.junit.jupiter.MockitoExtension;"
        }
        # A simple way to guess imports from dependencies
        for dep in dependencies:
            if '.' in dep['type'] and not dep['type'].startswith('java.lang'):
                 imports.add(f"import {dep['type']};")


        mock_fields = "\n    ".join([f"@Mock\n    private {d['type'].split('.')[-1]} {d['name']};" for d in dependencies])
        
        code = f"""package {package_name};

{' '.join(sorted(list(imports)))}

@ExtendWith(MockitoExtension.class)
class {class_name}Test {{

    {mock_fields}

    @InjectMocks
    private {class_name} {class_name[0].lower() + class_name[1:]};

    @BeforeEach
    void setUp() {{
        MockitoAnnotations.openMocks(this);
    }}

    // --- Generated Test Methods ---
    // AI finalization failed. The following snippets are combined manually.
    // They may require manual correction.
{combined_snippets}
}}
"""
        return code

    def _generate_tests_chunked(self, java_code, class_name, package_name, model_type, methods):
        """Generates tests by breaking the class into method chunks and then combining the results."""
        # Chunk methods into groups of 4 to manage prompt size
        method_chunks = [methods[i:i + 4] for i in range(0, len(methods), 4)]
        logger.info(f"Splitting {len(methods)} methods of {class_name} into {len(method_chunks)} chunks.")

        generated_test_snippets = []
        for i, chunk in enumerate(method_chunks):
            logger.info(f"Generating tests for chunk {i+1}/{len(method_chunks)}...")
            chunk_prompt = self._create_chunk_generation_prompt(java_code, class_name, package_name, chunk)
            try:
                response = self.generate_with_deepseek_v2(chunk_prompt, max_tokens=2048)
                snippet = response['choices'][0]['text']
                # Basic cleaning of the snippet
                snippet = re.sub(r'```java\n?', '', snippet.strip())
                snippet = re.sub(r'```', '', snippet)
                generated_test_snippets.append(snippet)
            except Exception as e:
                logger.error(f"Failed to generate tests for chunk {i+1}: {e}")
                method_names = ", ".join([m['name'] for m in chunk])
                generated_test_snippets.append(f"\n    // AI failed to generate tests for methods: {method_names}\n")
        
        logger.info("Combining and finalizing all generated test snippets.")
        combined_snippets = "\n\n".join(generated_test_snippets)
        
        finalization_prompt = self._create_finalization_prompt(java_code, class_name, package_name, combined_snippets)
        
        try:
            final_response = self.generate_with_deepseek_v2(finalization_prompt, max_tokens=8192)
            final_code = final_response['choices'][0]['text']
            return self._clean_generated_code(final_code, class_name)
        except Exception as e:
            logger.error(f"Final test formatting failed for {class_name}: {e}")
            return self._stitch_snippets_manually(java_code, class_name, package_name, combined_snippets)

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
        
        line_count = len(java_code.split('\n'))
        methods = self._extract_methods_with_details(java_code)
        
        # Heuristic: if the class is small (under 150 lines and < 5 methods), use single-shot.
        # Otherwise, use the more robust chunking approach.
        if line_count < 150 and len(methods) < 5:
            logger.info(f"Class '{class_name}' is small ({line_count} lines, {len(methods)} methods). Using single-shot generation.")
            return self._generate_tests_single_shot(java_code, class_name, package_name, model_type)
        
        logger.info(f"Class '{class_name}' is large ({line_count} lines, {len(methods)} methods). Using chunked generation.")
        return self._generate_tests_chunked(java_code, class_name, package_name, model_type, methods)

    def _generate_tests_single_shot(self, java_code, class_name, package_name, model_type):
        """
        Generates a complete test class in a single request to the AI model.
        This method constructs a highly detailed and strict prompt to ensure
        the AI generates comprehensive and complete test coverage.
        """
        dependencies = self._extract_dependencies(java_code)
        methods_to_test = self._extract_methods(java_code)
        method_list_str = "\n- ".join(methods_to_test) if methods_to_test else "No public methods found."

        prompt = f"""You are a senior Java test automation engineer. Your mission is to write a production-ready, comprehensive, and complete JUnit 5 test class for the provided Java code.

### Java Class to Test
```java
package {package_name};

{java_code}
```

### Class to be Tested: `{class_name}`

### Public Methods to Test:
You are required to generate tests for the following public methods:
- {method_list_str}

### STRICT INSTRUCTIONS:
1.  **FULL COVERAGE IS MANDATORY:** You MUST write test cases for EVERY single public method listed above. No exceptions.
2.  **NO INCOMPLETE CODE:** You MUST NOT generate partial code, placeholder comments (`// TODO`, `// ...`), or any comments suggesting that more tests are needed. The generated test class must be complete and final.
3.  **COMPLETE & RUNNABLE FILE:** The output must be a single, complete, and runnable Java file. It must start with the package declaration (`package {package_name};`) and include all necessary imports for JUnit 5, Mockito, and the classes under test.
4.  **MOCKING:**
    - The test class MUST be annotated with `@ExtendWith(MockitoExtension.class)`.
    - Use `@Mock` for all dependencies. Detected dependencies are: {', '.join([d['type'].split('.')[-1] + ' ' + d['name'] for d in dependencies]) or 'None'}.
    - Use `@InjectMocks` for the class under test: `private {class_name} {class_name[0].lower() + class_name[1:]};`.
5.  **TEST METHOD REQUIREMENTS:**
    - **Naming:** Follow the `test<MethodName>_<Scenario>` convention (e.g., `testHealth_Success`, `testInitializeModel_Failure`).
    - **Scenarios:** For each method, provide:
        - At least one **positive test** (happy path).
        - **Negative tests** for failure modes (e.g., invalid inputs, exceptions). Use `assertThrows`.
        - **Edge case tests** where applicable (e.g., null inputs, empty lists).
    - **Structure:** Strictly follow the **Arrange-Act-Assert** pattern, marked with comments (`// Arrange`, `// Act`, `// Assert`).
    - **Verification:** Verify mock interactions using `verify()` (e.g., `verify(myMock, times(1)).someMethod(any());`).

### Final Command
Generate the complete and final JUnit 5 test class for `{class_name}` now.
"""
        
        try:
            logger.info(f"Generating single-shot tests for {class_name} with a strict prompt.")
            # The model type selection is handled here for future extension,
            # but currently, it always defaults to the V2 model if available.
            if model_type == '6b' and self.deepseek_6b_initialized:
                 raise NotImplementedError("Local 6.7B model generation is not fully implemented here.")
            else:
                 response = self.generate_with_deepseek_v2(prompt, max_tokens=8192) # Increased max_tokens
                 generated_text = response['choices'][0]['text']

            # Clean the generated code to ensure it's a valid Java file
            return self._clean_generated_code(generated_text, class_name)
                
        except Exception as e:
            logger.error(f"Single-shot test generation failed for {class_name}: {e}")
            return self._generate_fallback_demo_class(class_name, package_name)

    def _extract_class_name(self, java_code):
        """Extracts the primary public class name from Java code."""
        # Regex to find public class, interface, or enum names
        name_match = re.search(r'public\s+(?:class|interface|enum)\s+([\w]+)', java_code)
        if name_match:
            return name_match.group(1)
            
        return None

    def _extract_methods(self, java_code):
        """Extracts public method names from Java code."""
        method_pattern = re.compile(r'public\s+(?!class|interface|enum|static\s+final)\s+[\w<>,?]+\s+([a-zA-Z]\w*)\s*\(')
        methods = method_pattern.findall(java_code)
        return methods

    def _clean_generated_code(self, generated_text, class_name):
        """
        Cleans the raw output from the AI model to produce a valid Java class file.
        """
        # Remove markdown fences and surrounding whitespace
        cleaned_text = re.sub(r'```java\n?', '', generated_text.strip())
        cleaned_text = re.sub(r'```', '', cleaned_text)
        
        # If the AI includes introductory text, find the start of the package declaration
        package_match = re.search(r'package\s+[\w.]+;', cleaned_text)
        if package_match:
            # Discard any text before the package declaration
            cleaned_text = cleaned_text[package_match.start():]
        else:
            # If no package declaration, the response is likely malformed
            logger.warning(f"Could not find package declaration in generated code for {class_name}.")
            # We can still try to return the text and hope it's usable
            return f"// AI Generation Error: Could not find package declaration.\n{cleaned_text}"

        return cleaned_text

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