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

    def _create_chunk_generation_prompt(self, java_code, class_name, package_name, method_chunk, additional_context=None):
        """Creates a prompt to generate tests for a small chunk of methods."""
        method_list = "\n".join([f"- `{m['return_type']} {m['name']}(...);`" for m in method_chunk])
        
        # Enhanced context section
        context_section = ""
        enhanced_guidance = ""
        flow_analysis_section = ""
        
        if additional_context:
            # Process DTOs and related Java files
            dto_files = {k: v for k, v in additional_context.items() if k.endswith('.java')}
            if dto_files:
                context_section += "\n### Available DTOs and Related Classes\n"
                for dto_name, dto_code in dto_files.items():
                    context_section += f"#### {dto_name}\n```java\n{dto_code}\n```\n\n"
            
            # Add package information if available
            if 'package_name' in additional_context:
                context_section += f"\n### Package Information\n```\nPackage: {additional_context['package_name']}\n```\n\n"
            
            # Add imports if available
            if 'imports' in additional_context:
                context_section += f"\n### Relevant Imports\n```java\n{additional_context['imports']}\n```\n\n"
            
            # Add class-specific guidance
            if 'class_characteristics' in additional_context:
                characteristics = additional_context['class_characteristics']
                enhanced_guidance = self._get_enhanced_test_guidance(characteristics)
                context_section += f"\n### Class-Specific Test Guidance\n{enhanced_guidance}\n\n"
            
            # Add flow analysis for targeted methods
            if 'flow_analysis' in additional_context:
                flow_analysis = additional_context['flow_analysis']
                method_names = [m['name'] for m in method_chunk]
                
                # Build targeted flow analysis for this chunk
                relevant_flows = {}
                for method_name in method_names:
                    if method_name in flow_analysis['method_flows']:
                        relevant_flows[method_name] = flow_analysis['method_flows'][method_name]
                
                if relevant_flows:
                    flow_analysis_section = "\n### DETAILED FLOW ANALYSIS FOR TARGET METHODS\n"
                    flow_analysis_section += "Use this analysis to generate comprehensive tests that cover all execution paths:\n\n"
                    
                    for method_name, flow_data in relevant_flows.items():
                        flow_analysis_section += f"#### Method: {method_name}\n"
                        
                        # Conditional branches
                        if method_name in flow_analysis['conditional_branches']:
                            branches = flow_analysis['conditional_branches'][method_name]
                            if branches.get('if_statements') or branches.get('switch_cases') or branches.get('ternary_operators'):
                                flow_analysis_section += "**Conditional Branches to Test:**\n"
                                for if_stmt in branches.get('if_statements', []):
                                    flow_analysis_section += f"- IF condition: `{if_stmt}` (test both true/false paths)\n"
                                for switch_case in branches.get('switch_cases', []):
                                    flow_analysis_section += f"- SWITCH case: `{switch_case}` (test each case + default)\n"
                                for ternary in branches.get('ternary_operators', []):
                                    flow_analysis_section += f"- TERNARY: `{ternary}` (test both conditions)\n"
                        
                        # Exception paths
                        if method_name in flow_analysis['exception_paths']:
                            exceptions = flow_analysis['exception_paths'][method_name]
                            if exceptions.get('thrown_exceptions') or exceptions.get('caught_exceptions'):
                                flow_analysis_section += "**Exception Scenarios to Test:**\n"
                                for thrown in exceptions.get('thrown_exceptions', []):
                                    flow_analysis_section += f"- Test exception: `{thrown}` (verify proper throwing)\n"
                                for caught in exceptions.get('caught_exceptions', []):
                                    flow_analysis_section += f"- Test catch block: `{caught}` (verify error handling)\n"
                        
                        # Dependency interactions
                        if method_name in flow_analysis['dependency_interactions']:
                            deps = flow_analysis['dependency_interactions'][method_name]
                            if deps.get('service_calls') or deps.get('repository_calls'):
                                flow_analysis_section += "**Dependency Interactions to Mock/Verify:**\n"
                                for service_call in deps.get('service_calls', []):
                                    flow_analysis_section += f"- Mock service call: `{service_call}`\n"
                                for repo_call in deps.get('repository_calls', []):
                                    flow_analysis_section += f"- Mock repository call: `{repo_call}`\n"
                        
                        flow_analysis_section += "\n"
            
            # Add any other context items
            other_context = {k: v for k, v in additional_context.items() 
                           if not k.endswith('.java') and k not in ['package_name', 'imports', 'class_characteristics', 'flow_analysis']}
            if other_context:
                context_section += "\n### Additional Context\n"
                for key, value in other_context.items():
                    context_section += f"#### {key}\n```\n{value}\n```\n\n"
        
        return f"""You are a Java test engineer with expertise in code flow analysis. Your task is to write comprehensive JUnit 5 test methods for a specific set of methods from a Java class.

### Full Class Context (for reference only)
```java
{java_code}
```

{context_section}

{flow_analysis_section}

### TARGET METHODS FOR TESTING:
Generate comprehensive tests for these methods ONLY:
{method_list}

### COMPREHENSIVE TEST GENERATION INSTRUCTIONS:

#### 1. FLOW-BASED TEST STRATEGY
**Use the flow analysis above to ensure complete coverage:**
- Test every conditional branch identified (if/else, switch cases, ternary operators)
- Test every exception path (both thrown and caught exceptions)
- Mock and verify every dependency interaction identified
- Test all data transformation scenarios
- Cover all validation points and edge cases

#### 2. TEST METHOD STRUCTURE
**For EACH method above, create multiple test scenarios:**

**A. Success/Happy Path Tests:**
- Test normal execution with valid inputs
- Test each conditional branch (true path)
- Verify correct return values and behavior

**B. Alternative Path Tests:**
- Test each conditional branch (false path)
- Test different switch case values
- Test ternary operator conditions

**C. Error/Exception Tests:**
- Test each identified exception scenario
- Test with null/invalid inputs (use `assertThrows`)
- Test external service failures
- Test validation failures

**D. Edge Case Tests:**
- Test with empty collections/strings
- Test boundary conditions
- Test concurrent scenarios if applicable

#### 3. ADVANCED MOCKING PATTERNS
**Static Method Mocking (when needed):**
```java
try (MockedStatic<ClassName> mockedStatic = mockStatic(ClassName.class)) {{
    mockedStatic.when(ClassName::staticMethod).thenReturn(value);
    // test code
}}
```

**Async/CompletableFuture Mocking:**
```java
CompletableFuture<Type> future = CompletableFuture.completedFuture(mockData);
when(asyncService.methodAsync(any())).thenReturn(future);
```

**Complex Exception Scenarios:**
```java
when(service.method(any())).thenThrow(new SpecificException("Detailed message"));
```

#### 4. MOCKING BEST PRACTICES
- **NEVER access private fields directly** (e.g., don't use `service.privateField`)
- Use `@Mock` annotations for dependencies, not direct field access
- Only mock methods that are actually used in the test
- Use `when().thenReturn()` for method stubbing
- Use `verify()` to verify mock interactions when needed
- Create realistic test data that matches production scenarios

#### 5. TEST NAMING AND ORGANIZATION
- Name tests as `testMethodName_Scenario_ExpectedResult` (e.g., `testGetSecuredLoans_ValidRequest_ReturnsSuccess`)
- Use `@DisplayName` for complex scenarios
- Group related assertions together
- Use descriptive test names that explain the scenario being tested

#### 6. ASSERTION PATTERNS
**Comprehensive Assertions:**
```java
// Verify return values
assertNotNull(result, "Result should not be null");
assertEquals(expectedValue, result.getValue(), "Value should match expected");

// Verify collections
assertEquals(expectedSize, result.getList().size(), "List size should match");
assertTrue(result.getList().contains(expectedItem), "List should contain expected item");

// Verify object state
assertEquals(expectedStatus, entity.getStatus(), "Status should be updated");
```

#### 7. VERIFICATION PATTERNS
**Method Call Verification:**
```java
verify(mockService).method(eq(expectedParam));
verify(mockService, times(2)).method(any());
verify(mockService, never()).method(any());
```

**Argument Capture (when needed):**
```java
ArgumentCaptor<Type> captor = ArgumentCaptor.forClass(Type.class);
verify(mockService).method(captor.capture());
assertEquals(expectedValue, captor.getValue().getField());
```

#### 8. TEST STRUCTURE TEMPLATE
```java
@Test
@DisplayName("Should handle scenario when condition occurs")
void testMethodName_Scenario_ExpectedResult() {{
    // Arrange
    InputType input = createValidInput();
    when(dependency.method(any())).thenReturn(expectedResult);
    
    // Act
    ResultType result = serviceUnderTest.methodName(input);
    
    // Assert
    assertNotNull(result);
    assertEquals(expectedValue, result.getValue());
    verify(dependency).method(eq(input));
}}
```

#### 9. QUALITY REQUIREMENTS
- Keep tests focused and simple
- Avoid unnecessary setup or teardown
- Don't create stubs for methods that aren't used
- Use meaningful test data that reflects real usage
- When DTOs are available, create realistic test data that matches their structure
- Test both synchronous and asynchronous scenarios
- Include transaction rollback testing for `@Transactional` methods

#### 10. COVERAGE GOALS
- Test every execution path identified in the flow analysis
- Test all exception scenarios found in the analysis
- Test edge cases and boundary conditions
- Verify all mock interactions identified in dependency analysis
- Test async operations and timeouts

Generate comprehensive, production-quality test methods now, following these strict guidelines and using the flow analysis data.
"""

    def _create_finalization_prompt(self, java_code, class_name, package_name, combined_snippets, additional_context=None):
        """Creates a prompt to combine and finalize the generated test snippets."""
        dependencies = self._extract_dependencies(java_code)
        dep_list = ", ".join([f"`{d['type']} {d['name']}`" for d in dependencies]) or "None"

        # Enhanced context section
        context_section = ""
        if additional_context:
            # Process DTOs and related Java files
            dto_files = {k: v for k, v in additional_context.items() if k.endswith('.java')}
            if dto_files:
                context_section += "\n### Available DTOs and Related Classes\n"
                for dto_name, dto_code in dto_files.items():
                    context_section += f"#### {dto_name}\n```java\n{dto_code}\n```\n\n"
            
            # Add package information if available
            if 'package_name' in additional_context:
                context_section += f"\n### Package Information\n```\nPackage: {additional_context['package_name']}\n```\n\n"
            
            # Add imports if available
            if 'imports' in additional_context:
                context_section += f"\n### Relevant Imports\n```java\n{additional_context['imports']}\n```\n\n"
            
            # Add any other context items
            other_context = {k: v for k, v in additional_context.items() 
                           if not k.endswith('.java') and k not in ['package_name', 'imports']}
            if other_context:
                context_section += "\n### Additional Context\n"
                for key, value in other_context.items():
                    context_section += f"#### {key}\n```\n{value}\n```\n\n"

        return f"""You are a senior Java test automation engineer. Your task is to assemble a complete and valid JUnit 5 test class from a set of generated test method snippets.

### Original Java Class to Test
```java
package {package_name};

{java_code}
```

{context_section}

### Detected Dependencies to Mock
{dep_list}

### Generated Test Method Snippets
Here are the generated test methods. They may be incomplete, contain errors, or lack context.
```java
{combined_snippets}
```

### STRICT INSTRUCTIONS
1. **Class Structure**:
   - Create a complete JUnit 5 test class named `{class_name}Test`.
   - Start with the correct package declaration: `package {package_name};`
   - Add ALL necessary imports (JUnit, Mockito, etc.).

2. **Mock Setup**:
   - Annotate the class with `@ExtendWith(MockitoExtension.class)`.
   - Create `@Mock` fields for ALL dependencies.
   - Create the `@InjectMocks` field for the class under test.
   - Add a `@BeforeEach` `setUp()` method with `MockitoAnnotations.openMocks(this);`.

3. **Test Method Integration**:
   - Place all provided test method snippets inside the class.
   - Fix any syntax errors and consolidate duplicate imports.
   - Ensure consistent formatting and that the code is complete.

4. **Mocking Best Practices**:
   - NEVER access private fields directly.
   - Use `@Mock` annotations for all dependencies.
   - Only mock methods that are actually used in tests.
   - Use `when().thenReturn()` for method stubbing.
   - Use `verify()` only when necessary.

5. **Code Quality**:
   - Remove any unnecessary stubs or verifications.
   - Keep tests focused and simple.
   - Use meaningful test data.
   - Follow the Arrange-Act-Assert pattern.
   - When DTOs are available, create realistic test data that matches their structure.

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

    def _generate_tests_chunked(self, java_code, class_name, package_name, model_type, methods, additional_context=None):
        """Generates tests by breaking the class into method chunks and then combining the results."""
        # Chunk methods into groups of 4 to manage prompt size
        method_chunks = [methods[i:i + 4] for i in range(0, len(methods), 4)]
        logger.info(f"Splitting {len(methods)} methods of {class_name} into {len(method_chunks)} chunks.")

        generated_test_snippets = []
        for i, chunk in enumerate(method_chunks):
            logger.info(f"Generating tests for chunk {i+1}/{len(method_chunks)}...")
            chunk_prompt = self._create_chunk_generation_prompt(java_code, class_name, package_name, chunk, additional_context)
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
        
        finalization_prompt = self._create_finalization_prompt(java_code, class_name, package_name, combined_snippets, additional_context)
        
        try:
            final_response = self.generate_with_deepseek_v2(finalization_prompt, max_tokens=8192)
            final_code = final_response['choices'][0]['text']
            return self._clean_generated_code(final_code, class_name)
        except Exception as e:
            logger.error(f"Final test formatting failed for {class_name}: {e}")
            return self._stitch_snippets_manually(java_code, class_name, package_name, combined_snippets)

    def generate_junit_tests(self, java_code, class_name=None, model_type="auto", additional_context=None):
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
        
        # Analyze class characteristics for better test generation
        characteristics = self._analyze_class_characteristics(java_code)
        
        # Perform detailed code flow analysis
        logger.info(f"Performing detailed code flow analysis for {class_name}...")
        flow_analysis = self._analyze_code_flow(java_code, class_name)
        
        # Log additional context if provided
        if additional_context:
            logger.info(f"Enhanced generation for {class_name} with {len(additional_context)} context items")
        
        logger.info(f"Class analysis for {class_name}: {characteristics['class_type']}, "
                   f"Transactions: {characteristics['has_transactions']}, "
                   f"Async: {characteristics['has_async_operations']}, "
                   f"External Services: {characteristics['has_external_services']}")
        
        # Log flow analysis summary
        total_methods_analyzed = len(flow_analysis['method_flows'])
        total_branches = sum(len(branches.get('if_statements', [])) for branches in flow_analysis['conditional_branches'].values())
        total_exceptions = sum(len(exceptions.get('thrown_exceptions', [])) for exceptions in flow_analysis['exception_paths'].values())
        
        logger.info(f"Flow analysis completed: {total_methods_analyzed} methods, "
                   f"{total_branches} conditional branches, {total_exceptions} exception paths")
        
        # Add characteristics and flow analysis to additional context
        if additional_context is None:
            additional_context = {}
        additional_context['class_characteristics'] = characteristics
        additional_context['flow_analysis'] = flow_analysis
        
        # For complex classes with detailed flow analysis, use the chunked approach
        # This ensures better handling of complex code with multiple methods and branches
        if total_methods_analyzed > 0 and (total_branches > 5 or total_exceptions > 2 or characteristics['has_async_operations']):
            logger.info(f"Class '{class_name}' has complex flow patterns. Using chunked generation with detailed analysis.")
            # Add flow analysis to context for chunked generation
            methods = self._extract_methods_with_details(java_code)
            return self._generate_tests_chunked(java_code, class_name, package_name, model_type, methods, additional_context)
        
        # Heuristic: if the class is small (under 150 lines and < 5 methods), use single-shot.
        # Otherwise, use the more robust chunking approach.
        if line_count < 150 and len(methods) < 5:
            logger.info(f"Class '{class_name}' is small ({line_count} lines, {len(methods)} methods). Using single-shot generation.")
            return self._generate_tests_single_shot(java_code, class_name, package_name, model_type, additional_context)
        
        logger.info(f"Class '{class_name}' is large ({line_count} lines, {len(methods)} methods). Using chunked generation.")
        return self._generate_tests_chunked(java_code, class_name, package_name, model_type, methods, additional_context)

    def _generate_tests_with_flow_analysis(self, java_code, class_name, package_name, model_type, flow_analysis, additional_context=None):
        """
        Generates tests using detailed code flow analysis for maximum accuracy.
        """
        try:
            logger.info(f"Generating tests with detailed flow analysis for {class_name}")
            
            # Create the enhanced prompt with flow analysis
            prompt = self._create_detailed_flow_analysis_prompt(java_code, class_name, package_name, flow_analysis, additional_context)
            
            # Use the V2 model with maximum tokens for comprehensive analysis
            if model_type == '6b' and self.deepseek_6b_initialized:
                raise NotImplementedError("Local 6.7B model generation is not fully implemented here.")
            else:
                response = self.generate_with_deepseek_v2(prompt, max_tokens=16384)  # Maximum tokens for detailed analysis
                generated_text = response['choices'][0]['text']

            # Clean the generated code to ensure it's a valid Java file
            return self._clean_generated_code(generated_text, class_name)
                
        except Exception as e:
            logger.error(f"Flow analysis test generation failed for {class_name}: {e}")
            # Fallback to regular single-shot generation
            logger.info(f"Falling back to regular single-shot generation for {class_name}")
            return self._generate_tests_single_shot(java_code, class_name, package_name, model_type, additional_context)

    def _generate_tests_single_shot(self, java_code, class_name, package_name, model_type, additional_context=None):
        """
        Generates a complete test class in a single request to the AI model.
        This method constructs a highly detailed and strict prompt to ensure
        the AI generates comprehensive and complete test coverage.
        """
        dependencies = self._extract_dependencies(java_code)
        methods_to_test = self._extract_methods(java_code)
        method_list_str = "\n- ".join(methods_to_test) if methods_to_test else "No public methods found."

        # Build additional context section for the prompt
        context_section = ""
        enhanced_guidance = ""
        
        if additional_context:
            # Process DTOs and related Java files
            dto_files = {k: v for k, v in additional_context.items() if k.endswith('.java')}
            if dto_files:
                context_section += "\n### Available DTOs and Related Classes\n"
                for dto_name, dto_code in dto_files.items():
                    context_section += f"#### {dto_name}\n```java\n{dto_code}\n```\n\n"
            
            # Add package information if available
            if 'package_name' in additional_context:
                context_section += f"\n### Package Information\n```\nPackage: {additional_context['package_name']}\n```\n\n"
            
            # Add imports if available
            if 'imports' in additional_context:
                context_section += f"\n### Relevant Imports\n```java\n{additional_context['imports']}\n```\n\n"
            
            # Add class-specific guidance
            if 'class_characteristics' in additional_context:
                characteristics = additional_context['class_characteristics']
                enhanced_guidance = self._get_enhanced_test_guidance(characteristics)
                context_section += f"\n### Class-Specific Test Guidance\n{enhanced_guidance}\n\n"

        prompt = f"""You are a senior Java test automation engineer. Your mission is to write a production-ready, comprehensive, and complete JUnit 5 test class for the provided Java code.

### Java Class to Test
```java
package {package_name};

{java_code}
```

{context_section}

### Class to be Tested: `{class_name}`

### Public Methods to Test:
You are required to generate tests for the following public methods:
- {method_list_str}

### COMPREHENSIVE TEST GENERATION INSTRUCTIONS:

#### 1. CLASS STRUCTURE & SETUP
- **Package & Imports**: Start with correct package declaration and ALL necessary imports
- **Annotations**: Use `@ExtendWith(MockitoExtension.class)` for the test class
- **Mock Setup**: Create `@Mock` fields for ALL dependencies: {', '.join([d['type'].split('.')[-1] + ' ' + d['name'] for d in dependencies]) or 'None'}
- **Class Under Test**: Use `@InjectMocks private {class_name} {class_name[0].lower() + class_name[1:]};`
- **Setup Method**: Include `@BeforeEach void setUp()` with `MockitoAnnotations.openMocks(this);`

#### 2. TEST METHOD REQUIREMENTS
**For EACH public method, generate multiple test scenarios:**

**A. Success/Happy Path Tests:**
- Test normal execution with valid inputs
- Test with typical data scenarios
- Verify correct return values and state changes

**B. Error/Exception Tests:**
- Test with null inputs (use `assertThrows`)
- Test with invalid data
- Test business logic exceptions
- Test external service failures

**C. Edge Case Tests:**
- Test with empty collections/strings
- Test boundary conditions
- Test concurrent scenarios if applicable

**D. Integration Scenarios:**
- Test method interactions with dependencies
- Test transaction rollback scenarios
- Test async operations if present

#### 3. ADVANCED MOCKING PATTERNS
**Static Method Mocking:**
```java
try (MockedStatic<ClassName> mockedStatic = mockStatic(ClassName.class)) {{
    mockedStatic.when(ClassName::staticMethod).thenReturn(value);
    // test code
}}
```

**Complex Object Mocking:**
- Create realistic test data that matches actual usage
- Use builder patterns when available
- Mock nested objects properly

**Async/CompletableFuture Mocking:**
```java
CompletableFuture<Type> future = CompletableFuture.completedFuture(mockData);
when(asyncService.methodAsync(any())).thenReturn(future);
```

**Exception Scenarios:**
```java
when(service.method(any())).thenThrow(new SpecificException("message"));
```

#### 4. VERIFICATION PATTERNS
**Method Call Verification:**
```java
verify(mockService).method(eq(expectedParam));
verify(mockService, times(2)).method(any());
verify(mockService, never()).method(any());
```

**Argument Capture:**
```java
ArgumentCaptor<Type> captor = ArgumentCaptor.forClass(Type.class);
verify(mockService).method(captor.capture());
assertEquals(expectedValue, captor.getValue().getField());
```

#### 5. TEST DATA CREATION
**Helper Methods:**
- Create private helper methods for test data creation
- Use realistic data that matches production scenarios
- Create both valid and invalid test data sets

**Example:**
```java
private EntityType createValidEntity() {{
    return EntityType.builder()
        .field1("validValue")
        .field2(123L)
        .build();
}}
```

#### 6. ASSERTION BEST PRACTICES
**Comprehensive Assertions:**
- Verify return values with specific assertions
- Check object state changes
- Verify collection contents and sizes
- Use custom assertion messages

**Examples:**
```java
assertEquals(expectedValue, actualValue, "Custom error message");
assertNotNull(result, "Result should not be null");
assertTrue(condition, "Condition should be true");
assertThat(list).hasSize(3).contains(expectedItem);
```

#### 7. TEST ORGANIZATION
**Naming Convention:**
- Use descriptive test names: `testMethodName_Scenario_ExpectedResult`
- Group related tests together
- Use `@DisplayName` for complex scenarios

**Test Structure:**
```java
@Test
@DisplayName("Should return success when valid data is provided")
void testMethodName_ValidData_ReturnsSuccess() {{
    // Arrange
    Type input = createValidInput();
    when(dependency.method(any())).thenReturn(expectedResult);
    
    // Act
    ResultType result = serviceUnderTest.methodName(input);
    
    // Assert
    assertNotNull(result);
    assertEquals(expectedValue, result.getValue());
    verify(dependency).method(eq(input));
}}
```

#### 8. COVERAGE REQUIREMENTS
**Ensure 100% method coverage:**
- Test every public method
- Test every branch/condition
- Test exception handling paths
- Test async/callback scenarios

**Transaction Testing:**
- Test `@Transactional` methods with rollback scenarios
- Verify database state changes
- Test concurrent access patterns

#### 9. PERFORMANCE & RESOURCE TESTING
- Test timeout scenarios
- Test with large data sets
- Verify resource cleanup
- Test memory usage patterns

### FINAL REQUIREMENTS:
1. **Complete Runnable Code**: Generate a full, compilable test class
2. **No Placeholders**: No TODO comments or incomplete methods
3. **Realistic Test Data**: Use meaningful test data that reflects real usage
4. **Comprehensive Coverage**: Test all scenarios, not just happy paths
5. **Production Quality**: Code should be maintainable and follow best practices

Generate the complete, comprehensive JUnit 5 test class now.
"""
        
        try:
            logger.info(f"Generating comprehensive single-shot tests for {class_name} with enhanced prompting.")
            # The model type selection is handled here for future extension,
            # but currently, it always defaults to the V2 model if available.
            if model_type == '6b' and self.deepseek_6b_initialized:
                 raise NotImplementedError("Local 6.7B model generation is not fully implemented here.")
            else:
                 response = self.generate_with_deepseek_v2(prompt, max_tokens=12288) # Increased max_tokens for comprehensive tests
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
        
    def _analyze_class_characteristics(self, java_code):
        """Analyzes the Java class to identify patterns that should influence test generation."""
        characteristics = {
            'has_transactions': False,
            'has_async_operations': False,
            'has_static_methods': False,
            'has_builders': False,
            'has_validation': False,
            'has_external_services': False,
            'has_database_operations': False,
            'class_type': self._get_class_type(java_code),
            'exception_types': [],
            'async_patterns': [],
            'validation_patterns': []
        }
        
        # Check for transactional methods
        if re.search(r'@Transactional', java_code):
            characteristics['has_transactions'] = True
        
        # Check for async operations
        async_patterns = [
            r'CompletableFuture',
            r'@Async',
            r'async\w*Service',
            r'\.runAsync\(',
            r'\.supplyAsync\(',
            r'applicationTaskExecutor'
        ]
        for pattern in async_patterns:
            if re.search(pattern, java_code):
                characteristics['has_async_operations'] = True
                characteristics['async_patterns'].append(pattern)
        
        # Check for static method calls
        if re.search(r'\w+\.\w+\(', java_code):
            characteristics['has_static_methods'] = True
        
        # Check for builder patterns
        if re.search(r'\.builder\(\)', java_code):
            characteristics['has_builders'] = True
        
        # Check for validation annotations
        validation_patterns = [
            r'@Valid',
            r'@NotNull',
            r'@NotEmpty',
            r'@Size',
            r'@Min',
            r'@Max',
            r'throw new.*Exception'
        ]
        for pattern in validation_patterns:
            if re.search(pattern, java_code):
                characteristics['has_validation'] = True
                characteristics['validation_patterns'].append(pattern)
        
        # Check for external service calls
        external_service_patterns = [
            r'restTemplate\.',
            r'webClient\.',
            r'httpClient\.',
            r'Service\w*\.get',
            r'Service\w*\.post',
            r'Service\w*\.call'
        ]
        for pattern in external_service_patterns:
            if re.search(pattern, java_code):
                characteristics['has_external_services'] = True
        
        # Check for database operations
        db_patterns = [
            r'Repository\w*\.',
            r'\.save\(',
            r'\.findBy',
            r'\.delete',
            r'@Query',
            r'EntityManager'
        ]
        for pattern in db_patterns:
            if re.search(pattern, java_code):
                characteristics['has_database_operations'] = True
        
        # Extract exception types
        exception_matches = re.findall(r'throw new (\w+Exception)', java_code)
        characteristics['exception_types'] = list(set(exception_matches))
        
        return characteristics

    def _get_enhanced_test_guidance(self, characteristics):
        """Generates specific test guidance based on class characteristics."""
        guidance = []
        
        if characteristics['has_transactions']:
            guidance.append("""
**Transaction Testing:**
- Test rollback scenarios with `@Transactional(rollbackFor = Exception.class)`
- Verify database state changes
- Test concurrent transaction scenarios
- Mock transaction manager if needed""")
        
        if characteristics['has_async_operations']:
            guidance.append("""
**Async Operation Testing:**
- Mock CompletableFuture operations: `CompletableFuture.completedFuture(mockData)`
- Test timeout scenarios: `CompletableFuture.failedFuture(new TimeoutException())`
- Verify async execution with `verify(executor).execute(any(Runnable.class))`
- Test exception handling in async operations""")
        
        if characteristics['has_external_services']:
            guidance.append("""
**External Service Testing:**
- Mock HTTP responses with different status codes
- Test connection timeouts and failures
- Test retry mechanisms
- Verify request parameters and headers""")
        
        if characteristics['has_database_operations']:
            guidance.append("""
**Database Operation Testing:**
- Mock repository methods with realistic return values
- Test entity not found scenarios
- Test constraint violations
- Verify save/update operations with argument captors""")
        
        if characteristics['has_validation']:
            guidance.append("""
**Validation Testing:**
- Test all validation failure scenarios
- Use `assertThrows` for validation exceptions
- Test edge cases for size/range validations
- Verify error messages are meaningful""")
        
        if characteristics['exception_types']:
            exception_list = ', '.join(characteristics['exception_types'])
            guidance.append(f"""
**Exception Scenario Testing:**
- Test all custom exceptions: {exception_list}
- Verify exception messages and error codes
- Test exception propagation
- Test error handling and recovery""")
        
        return '\n'.join(guidance)

    def _analyze_code_flow(self, java_code, class_name):
        """Performs detailed code flow analysis to understand method execution paths."""
        flow_analysis = {
            'method_flows': {},
            'conditional_branches': {},
            'exception_paths': {},
            'dependency_interactions': {},
            'data_transformations': {},
            'validation_points': {},
            'async_operations': {},
            'transaction_boundaries': {}
        }
        
        # Extract all methods with their bodies
        method_pattern = re.compile(
            r'(public|private|protected)\s+(?:static\s+)?(?:final\s+)?([\w<>,.?\s\[\]]+)\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*(?:throws\s+[\w,.\s]+)?\s*\{',
            re.MULTILINE
        )
        
        methods = method_pattern.finditer(java_code)
        
        for method_match in methods:
            visibility = method_match.group(1)
            return_type = method_match.group(2).strip()
            method_name = method_match.group(3)
            parameters = method_match.group(4).strip()
            
            # Skip if not public method
            if visibility != 'public':
                continue
                
            # Find method body
            method_start = method_match.end()
            method_body = self._extract_method_body(java_code, method_start)
            
            if method_body:
                flow_analysis['method_flows'][method_name] = self._analyze_method_flow(method_body, method_name)
                flow_analysis['conditional_branches'][method_name] = self._find_conditional_branches(method_body)
                flow_analysis['exception_paths'][method_name] = self._find_exception_paths(method_body)
                flow_analysis['dependency_interactions'][method_name] = self._find_dependency_calls(method_body)
                flow_analysis['data_transformations'][method_name] = self._find_data_transformations(method_body)
                flow_analysis['validation_points'][method_name] = self._find_validation_points(method_body)
                flow_analysis['async_operations'][method_name] = self._find_async_operations(method_body)
                flow_analysis['transaction_boundaries'][method_name] = self._find_transaction_boundaries(method_body)
        
        return flow_analysis
    
    def _extract_method_body(self, java_code, start_pos):
        """Extracts the complete method body by matching braces."""
        brace_count = 0
        in_string = False
        escape_next = False
        i = start_pos
        
        # Find the opening brace
        while i < len(java_code) and java_code[i] != '{':
            i += 1
        
        if i >= len(java_code):
            return None
            
        method_start = i
        brace_count = 1
        i += 1
        
        while i < len(java_code) and brace_count > 0:
            char = java_code[i]
            
            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
            
            i += 1
        
        if brace_count == 0:
            return java_code[method_start:i]
        
        return None
    
    def _analyze_method_flow(self, method_body, method_name):
        """Analyzes the execution flow within a method."""
        flow_info = {
            'entry_points': 1,
            'exit_points': [],
            'loops': [],
            'recursive_calls': [],
            'early_returns': [],
            'complexity_score': 1
        }
        
        # Find return statements
        return_pattern = re.compile(r'\breturn\b(?:\s+[^;]+)?;')
        returns = return_pattern.findall(method_body)
        flow_info['exit_points'] = returns
        flow_info['early_returns'] = [r for r in returns if 'return' in r and not r.strip().endswith('return;')]
        
        # Find loops
        loop_patterns = [
            r'\bfor\s*\([^)]*\)',
            r'\bwhile\s*\([^)]*\)',
            r'\bdo\s*\{.*?\}\s*while\s*\([^)]*\)'
        ]
        for pattern in loop_patterns:
            loops = re.findall(pattern, method_body, re.DOTALL)
            flow_info['loops'].extend(loops)
        
        # Find recursive calls
        if method_name in method_body:
            recursive_calls = re.findall(rf'\b{method_name}\s*\(', method_body)
            flow_info['recursive_calls'] = recursive_calls
        
        # Calculate cyclomatic complexity
        decision_points = len(re.findall(r'\b(if|else|while|for|case|catch|&&|\|\|)\b', method_body))
        flow_info['complexity_score'] = decision_points + 1
        
        return flow_info
    
    def _find_conditional_branches(self, method_body):
        """Finds all conditional branches and their conditions."""
        branches = {
            'if_statements': [],
            'switch_cases': [],
            'ternary_operators': [],
            'null_checks': [],
            'empty_checks': []
        }
        
        # Find if statements with conditions
        if_pattern = re.compile(r'if\s*\(([^)]+)\)', re.MULTILINE)
        if_matches = if_pattern.findall(method_body)
        branches['if_statements'] = if_matches
        
        # Find switch cases
        switch_pattern = re.compile(r'switch\s*\([^)]+\).*?case\s+([^:]+):', re.DOTALL)
        switch_matches = switch_pattern.findall(method_body)
        branches['switch_cases'] = switch_matches
        
        # Find ternary operators
        ternary_pattern = re.compile(r'([^?]+)\s*\?\s*([^:]+)\s*:\s*([^;,)]+)')
        ternary_matches = ternary_pattern.findall(method_body)
        branches['ternary_operators'] = ternary_matches
        
        # Find null checks
        null_checks = re.findall(r'(\w+)\s*[!=]=\s*null', method_body)
        branches['null_checks'] = null_checks
        
        # Find empty/blank checks
        empty_checks = re.findall(r'(\w+)\.isEmpty\(\)|StringUtils\.isBlank\((\w+)\)|CollectionUtils\.isEmpty\((\w+)\)', method_body)
        branches['empty_checks'] = [check for check_tuple in empty_checks for check in check_tuple if check]
        
        return branches
    
    def _find_exception_paths(self, method_body):
        """Finds exception handling and throwing patterns."""
        exceptions = {
            'thrown_exceptions': [],
            'caught_exceptions': [],
            'finally_blocks': [],
            'custom_exceptions': []
        }
        
        # Find throw statements
        throw_pattern = re.compile(r'throw\s+new\s+(\w+(?:Exception|Error))\s*\([^)]*\)')
        thrown = throw_pattern.findall(method_body)
        exceptions['thrown_exceptions'] = thrown
        
        # Find catch blocks
        catch_pattern = re.compile(r'catch\s*\(\s*(\w+(?:Exception|Error))\s+\w+\s*\)')
        caught = catch_pattern.findall(method_body)
        exceptions['caught_exceptions'] = caught
        
        # Find finally blocks
        finally_pattern = re.compile(r'finally\s*\{')
        finally_blocks = finally_pattern.findall(method_body)
        exceptions['finally_blocks'] = finally_blocks
        
        # Find custom exception types
        custom_exception_pattern = re.compile(r'throw\s+new\s+(\w+Exception)\s*\([^)]*\)')
        custom_exceptions = custom_exception_pattern.findall(method_body)
        exceptions['custom_exceptions'] = list(set(custom_exceptions))
        
        return exceptions
    
    def _find_dependency_calls(self, method_body):
        """Finds calls to injected dependencies and external services."""
        dependency_calls = {
            'repository_calls': [],
            'service_calls': [],
            'external_api_calls': [],
            'static_method_calls': [],
            'builder_usages': []
        }
        
        # Find repository method calls
        repo_pattern = re.compile(r'(\w+Repository)\.(\w+)\s*\(')
        repo_calls = repo_pattern.findall(method_body)
        dependency_calls['repository_calls'] = repo_calls
        
        # Find service method calls
        service_pattern = re.compile(r'(\w+Service)\.(\w+)\s*\(')
        service_calls = service_pattern.findall(method_body)
        dependency_calls['service_calls'] = service_calls
        
        # Find external API calls
        api_pattern = re.compile(r'(restTemplate|webClient|httpClient)\.(\w+)\s*\(')
        api_calls = api_pattern.findall(method_body)
        dependency_calls['external_api_calls'] = api_calls
        
        # Find static method calls
        static_pattern = re.compile(r'([A-Z]\w+)\.(\w+)\s*\(')
        static_calls = static_pattern.findall(method_body)
        dependency_calls['static_method_calls'] = static_calls
        
        # Find builder pattern usage
        builder_pattern = re.compile(r'(\w+)\.builder\(\)')
        builder_calls = builder_pattern.findall(method_body)
        dependency_calls['builder_usages'] = builder_calls
        
        return dependency_calls
    
    def _find_data_transformations(self, method_body):
        """Finds data mapping, conversion, and transformation operations."""
        transformations = {
            'mappers': [],
            'stream_operations': [],
            'conversions': [],
            'collections_operations': []
        }
        
        # Find mapper calls
        mapper_pattern = re.compile(r'(\w+Mapper)\.(\w+)\s*\(')
        mapper_calls = mapper_pattern.findall(method_body)
        transformations['mappers'] = mapper_calls
        
        # Find stream operations
        stream_pattern = re.compile(r'\.stream\(\)\.(\w+)\(')
        stream_ops = stream_pattern.findall(method_body)
        transformations['stream_operations'] = stream_ops
        
        # Find type conversions
        conversion_pattern = re.compile(r'(\w+)\.valueOf\(|(\w+)\.parse\w+\(|new\s+(\w+)\(')
        conversions = conversion_pattern.findall(method_body)
        transformations['conversions'] = [conv for conv_tuple in conversions for conv in conv_tuple if conv]
        
        # Find collection operations
        collection_pattern = re.compile(r'(\w+)\.add\(|(\w+)\.remove\(|(\w+)\.put\(|(\w+)\.get\(')
        collection_ops = collection_pattern.findall(method_body)
        transformations['collections_operations'] = [op for op_tuple in collection_ops for op in op_tuple if op]
        
        return transformations
    
    def _find_validation_points(self, method_body):
        """Finds validation logic and assertion points."""
        validations = {
            'null_validations': [],
            'empty_validations': [],
            'business_validations': [],
            'parameter_validations': []
        }
        
        # Find null validations
        null_validations = re.findall(r'if\s*\(\s*(\w+)\s*==\s*null\s*\)', method_body)
        validations['null_validations'] = null_validations
        
        # Find empty validations
        empty_validations = re.findall(r'if\s*\(\s*(\w+)\.isEmpty\(\)\s*\)', method_body)
        validations['empty_validations'] = empty_validations
        
        # Find business validation patterns
        business_validations = re.findall(r'if\s*\(\s*!?(\w+\.\w+\([^)]*\))\s*\)', method_body)
        validations['business_validations'] = business_validations
        
        return validations
    
    def _find_async_operations(self, method_body):
        """Finds asynchronous operations and patterns."""
        async_ops = {
            'completable_futures': [],
            'async_method_calls': [],
            'executor_usage': [],
            'timeout_operations': []
        }
        
        # Find CompletableFuture operations
        cf_pattern = re.compile(r'CompletableFuture\.(\w+)\(')
        cf_ops = cf_pattern.findall(method_body)
        async_ops['completable_futures'] = cf_ops
        
        # Find async method calls
        async_pattern = re.compile(r'(\w+Async)\s*\(')
        async_calls = async_pattern.findall(method_body)
        async_ops['async_method_calls'] = async_calls
        
        # Find executor usage
        executor_pattern = re.compile(r'(\w*[Ee]xecutor)\.(\w+)\s*\(')
        executor_calls = executor_pattern.findall(method_body)
        async_ops['executor_usage'] = executor_calls
        
        return async_ops
    
    def _find_transaction_boundaries(self, method_body):
        """Finds transaction-related operations."""
        transactions = {
            'save_operations': [],
            'delete_operations': [],
            'update_operations': [],
            'rollback_points': []
        }
        
        # Find save operations
        save_pattern = re.compile(r'(\w+)\.save\s*\(')
        save_ops = save_pattern.findall(method_body)
        transactions['save_operations'] = save_ops
        
        # Find delete operations
        delete_pattern = re.compile(r'(\w+)\.delete\s*\(')
        delete_ops = delete_pattern.findall(method_body)
        transactions['delete_operations'] = delete_ops
        
        return transactions

    def _create_detailed_flow_analysis_prompt(self, java_code, class_name, package_name, flow_analysis, additional_context=None):
        """Creates a comprehensive prompt with detailed code flow analysis."""
        
        # Build flow analysis summary
        flow_summary = self._build_flow_analysis_summary(flow_analysis)
        
        # Enhanced context section
        context_section = ""
        if additional_context:
            # Process DTOs and related Java files
            dto_files = {k: v for k, v in additional_context.items() if k.endswith('.java')}
            if dto_files:
                context_section += "\n### Available DTOs and Related Classes\n"
                for dto_name, dto_code in dto_files.items():
                    context_section += f"#### {dto_name}\n```java\n{dto_code}\n```\n\n"
            
            # Add package information if available
            if 'package_name' in additional_context:
                context_section += f"\n### Package Information\n```\nPackage: {additional_context['package_name']}\n```\n\n"
            
            # Add imports if available
            if 'imports' in additional_context:
                context_section += f"\n### Relevant Imports\n```java\n{additional_context['imports']}\n```\n\n"
            
            # Add class-specific guidance
            if 'class_characteristics' in additional_context:
                characteristics = additional_context['class_characteristics']
                enhanced_guidance = self._get_enhanced_test_guidance(characteristics)
                context_section += f"\n### Class-Specific Test Guidance\n{enhanced_guidance}\n\n"

        return f"""You are a senior Java test automation engineer with expertise in code flow analysis. Your mission is to write comprehensive JUnit 5 tests based on detailed analysis of the source code execution paths.

### Java Class to Test
```java
package {package_name};

{java_code}
```

{context_section}

### DETAILED CODE FLOW ANALYSIS
{flow_summary}

### COMPREHENSIVE TEST GENERATION STRATEGY

#### PHASE 1: CODE PATH ANALYSIS
Based on the detailed flow analysis above, you must:

1. **Identify All Execution Paths**: For each method, trace through every possible execution path
2. **Map Decision Points**: Test each conditional branch, switch case, and ternary operator
3. **Validate Exception Scenarios**: Test every exception path and error condition
4. **Verify Data Transformations**: Test all mapping, conversion, and stream operations
5. **Test Dependency Interactions**: Mock and verify every external service call
6. **Validate Async Operations**: Test all CompletableFuture and async scenarios

#### PHASE 2: TEST SCENARIO GENERATION
For each method, generate tests for:

**A. Primary Execution Paths:**
- Happy path with valid inputs
- Each conditional branch (true/false scenarios)
- All switch case values
- Loop iterations (empty, single, multiple items)

**B. Exception and Error Paths:**
- Every thrown exception type identified in analysis
- Null pointer scenarios for each null check
- Empty collection/string scenarios
- Validation failure points
- External service failure scenarios

**C. Data Flow Testing:**
- Input validation at entry points
- Data transformation accuracy
- Output verification at exit points
- State changes in entities/objects

**D. Integration Testing:**
- Repository interaction patterns
- Service call sequences
- Transaction boundary testing
- Async operation completion/timeout

#### PHASE 3: ADVANCED TEST PATTERNS

**Static Method Mocking (for identified static calls):**
```java
try (MockedStatic<StaticClassName> mockedStatic = mockStatic(StaticClassName.class)) {{
    mockedStatic.when(StaticClassName::methodName).thenReturn(expectedValue);
    // test execution
}}
```

**Async Operation Testing (for identified async patterns):**
```java
// For CompletableFuture operations
CompletableFuture<Type> future = CompletableFuture.completedFuture(mockData);
when(asyncService.methodAsync(any())).thenReturn(future);

// For timeout scenarios
CompletableFuture<Type> timeoutFuture = new CompletableFuture<>();
timeoutFuture.completeExceptionally(new TimeoutException("Service timeout"));
when(asyncService.methodAsync(any())).thenReturn(timeoutFuture);
```

**Repository/Database Testing (for identified data operations):**
```java
// Test save operations
ArgumentCaptor<EntityType> entityCaptor = ArgumentCaptor.forClass(EntityType.class);
verify(repository).save(entityCaptor.capture());
assertEquals(expectedValue, entityCaptor.getValue().getField());

// Test find operations
when(repository.findById(anyLong())).thenReturn(Optional.of(mockEntity));
when(repository.findById(anyLong())).thenReturn(Optional.empty()); // Not found scenario
```

#### PHASE 4: COMPREHENSIVE VERIFICATION

**Method Call Verification (based on dependency analysis):**
```java
// Verify exact method calls identified in flow analysis
verify(dependencyService).specificMethod(eq(expectedParam));
verify(repository, times(2)).save(any(EntityType.class));
verify(externalService, never()).unnecessaryMethod(any());
```

**State Verification (based on data transformation analysis):**
```java
// Verify object state changes
assertEquals(expectedStatus, entity.getStatus());
assertEquals(expectedSize, resultList.size());
assertTrue(resultList.contains(expectedItem));
```

#### PHASE 5: TEST ORGANIZATION AND STRUCTURE

**Test Class Structure:**
```java
@ExtendWith(MockitoExtension.class)
class {class_name}Test {{
    
    // Mock all identified dependencies
    @Mock private DependencyType dependency;
    
    @InjectMocks
    private {class_name} {class_name.lower()};
    
    @BeforeEach
    void setUp() {{
        MockitoAnnotations.openMocks(this);
    }}
    
    // Helper methods for test data creation
    private EntityType createValidEntity() {{
        return EntityType.builder()
            .field1("validValue")
            .field2(123L)
            .build();
    }}
    
    // Test methods following the analysis
}}
```

**Test Method Naming Convention:**
- `testMethodName_ConditionScenario_ExpectedResult`
- `testMethodName_ExceptionType_ThrowsException`
- `testMethodName_EdgeCase_HandlesCorrectly`

### FINAL REQUIREMENTS:

1. **100% Path Coverage**: Test every execution path identified in the flow analysis
2. **Exception Completeness**: Test every exception scenario found in the code
3. **Dependency Verification**: Mock and verify every external interaction
4. **Data Accuracy**: Validate all data transformations and state changes
5. **Async Handling**: Properly test all asynchronous operations
6. **Production Quality**: Generate maintainable, readable, and comprehensive tests

Generate the complete, comprehensive JUnit 5 test class that covers all identified code paths and scenarios.
"""

    def _build_flow_analysis_summary(self, flow_analysis):
        """Builds a comprehensive summary of the code flow analysis."""
        summary_parts = []
        
        for method_name, flow_info in flow_analysis['method_flows'].items():
            summary_parts.append(f"\n#### Method: {method_name}")
            summary_parts.append(f"**Complexity Score**: {flow_info['complexity_score']}")
            summary_parts.append(f"**Exit Points**: {len(flow_info['exit_points'])}")
            
            if flow_info['early_returns']:
                summary_parts.append(f"**Early Returns**: {len(flow_info['early_returns'])} (test each return condition)")
            
            if flow_info['loops']:
                summary_parts.append(f"**Loops Found**: {len(flow_info['loops'])} (test empty, single, multiple iterations)")
            
            # Conditional branches
            if method_name in flow_analysis['conditional_branches']:
                branches = flow_analysis['conditional_branches'][method_name]
                if branches['if_statements']:
                    summary_parts.append(f"**If Conditions**: {branches['if_statements']} (test true/false for each)")
                if branches['null_checks']:
                    summary_parts.append(f"**Null Checks**: {branches['null_checks']} (test null/non-null scenarios)")
                if branches['empty_checks']:
                    summary_parts.append(f"**Empty Checks**: {branches['empty_checks']} (test empty/non-empty scenarios)")
            
            # Exception paths
            if method_name in flow_analysis['exception_paths']:
                exceptions = flow_analysis['exception_paths'][method_name]
                if exceptions['thrown_exceptions']:
                    summary_parts.append(f"**Thrown Exceptions**: {exceptions['thrown_exceptions']} (test each exception scenario)")
                if exceptions['caught_exceptions']:
                    summary_parts.append(f"**Caught Exceptions**: {exceptions['caught_exceptions']} (test exception handling)")
            
            # Dependency interactions
            if method_name in flow_analysis['dependency_interactions']:
                deps = flow_analysis['dependency_interactions'][method_name]
                if deps['repository_calls']:
                    summary_parts.append(f"**Repository Calls**: {deps['repository_calls']} (mock and verify each)")
                if deps['service_calls']:
                    summary_parts.append(f"**Service Calls**: {deps['service_calls']} (mock and verify each)")
                if deps['external_api_calls']:
                    summary_parts.append(f"**External API Calls**: {deps['external_api_calls']} (test success/failure scenarios)")
                if deps['static_method_calls']:
                    summary_parts.append(f"**Static Method Calls**: {deps['static_method_calls']} (use MockedStatic)")
            
            # Data transformations
            if method_name in flow_analysis['data_transformations']:
                transforms = flow_analysis['data_transformations'][method_name]
                if transforms['mappers']:
                    summary_parts.append(f"**Mapper Calls**: {transforms['mappers']} (verify mapping accuracy)")
                if transforms['stream_operations']:
                    summary_parts.append(f"**Stream Operations**: {transforms['stream_operations']} (test with various data sets)")
            
            # Async operations
            if method_name in flow_analysis['async_operations']:
                async_ops = flow_analysis['async_operations'][method_name]
                if async_ops['completable_futures']:
                    summary_parts.append(f"**Async Operations**: {async_ops['completable_futures']} (test completion/timeout/exception)")
                if async_ops['executor_usage']:
                    summary_parts.append(f"**Executor Usage**: {async_ops['executor_usage']} (verify async execution)")
            
            # Transaction boundaries
            if method_name in flow_analysis['transaction_boundaries']:
                transactions = flow_analysis['transaction_boundaries'][method_name]
                if transactions['save_operations']:
                    summary_parts.append(f"**Save Operations**: {transactions['save_operations']} (verify data persistence)")
                if transactions['delete_operations']:
                    summary_parts.append(f"**Delete Operations**: {transactions['delete_operations']} (verify data removal)")
        
        return '\n'.join(summary_parts)


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
    # NEW: Extract additional context (DTOs, imports, etc.)
    additional_context = data.get('additional_context', {})
        
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
        if additional_context:
            logger.info(f"Additional context provided: {list(additional_context.keys())}")
        
        # Check if Ollama is available before proceeding
        if model_type != '6b' and not generator.check_ollama_running():
            logger.warning("Ollama is not running. Attempting to generate with fallback methods.")
            # Try to generate anyway, the fallback will kick in during chunk processing
        
        generated_tests = generator.generate_junit_tests(java_code, class_name, model_type, additional_context)
        
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
            "context_items_used": len(additional_context) if additional_context else 0,
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