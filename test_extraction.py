#!/usr/bin/env python3

import sys
sys.path.append('.')
from deepseek_coder_server import DeepSeekV2Generator

# Read the test file
with open('test_sample_simple.java', 'r') as f:
    java_code = f.read()

# Create generator instance
generator = DeepSeekV2Generator()

# Test method extraction
print("=== TESTING METHOD EXTRACTION ===")
methods = generator._extract_methods_with_details(java_code)
print(f'Found {len(methods)} methods:')
for method in methods:
    print(f'  - Method: {method["name"]}')

# Test dependency extraction
print("\n=== TESTING DEPENDENCY EXTRACTION ===")
dependencies = generator._extract_dependencies(java_code)
print(f'Found {len(dependencies)} dependencies:')
for dep in dependencies:
    print(f'  - Dependency: {dep["type"]} {dep["name"]}')

# Test class name extraction
print("\n=== TESTING CLASS NAME EXTRACTION ===")
class_name = generator._extract_class_name(java_code)
print(f'Class name: {class_name}')

print("\n=== TESTING PROMPT GENERATION ===")
# Test the prompt generation
dependencies_declarations = ""
if dependencies:
    for dep in dependencies:
        dependencies_declarations += f"    - `{dep['type']} {dep['name']}`\n"
else:
    dependencies_declarations = "    - None\n"

prompt = generator.single_shot_prompt_template.format(
    class_name=class_name,
    dependencies_declarations=dependencies_declarations,
    original_java_code=java_code
)

print("Generated prompt length:", len(prompt))
print("First 500 chars of prompt:")
print(prompt[:500]) 