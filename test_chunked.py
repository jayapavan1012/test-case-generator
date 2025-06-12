#!/usr/bin/env python3

import sys
sys.path.append('.')
from deepseek_coder_server import DeepSeekV2Generator

# Read the test file
with open('test_sample_simple.java', 'r') as f:
    java_code = f.read()

# Create generator instance
generator = DeepSeekV2Generator()

print("=== TESTING CHUNKED APPROACH ===")
print(f"Original code length: {len(java_code)} characters")
print(f"Original code lines: {len(java_code.split(chr(10)))}")

# Test chunking
chunks = generator._split_code_into_chunks(java_code, lines_per_chunk=15)  # Small chunks for testing
print(f"\n📝 Split into {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i+1}: lines {chunk['start_line']}-{chunk['end_line']} ({chunk['line_count']} lines)")
    methods = generator._extract_methods_with_details(chunk['code'])
    print(f"    Methods found: {[m['name'] for m in methods]}")

# Test dependencies
dependencies = generator._extract_dependencies(java_code)
deps_formatted = generator._format_dependencies_for_prompt(dependencies)
print(f"\n=== DEPENDENCIES ===")
print(deps_formatted)

# Test class name
class_name = generator._extract_class_name(java_code)
print(f"\n=== CLASS NAME ===")
print(f"Extracted class name: {class_name}")

print("\n=== TESTING CHUNK PROMPT GENERATION ===")
if chunks:
    first_chunk = chunks[0]
    methods_in_chunk = generator._extract_methods_with_details(first_chunk['code'])
    if methods_in_chunk:
        print(f"First chunk has {len(methods_in_chunk)} methods: {[m['name'] for m in methods_in_chunk]}")
        
        # Show what the chunk prompt would look like
        chunk_prompt = f"""You are an expert Java test engineer. Generate JUnit 5 test methods for the specific methods found in this code chunk.

### CRITICAL REQUIREMENTS:
1. Generate ONLY @Test methods (no class declaration, no imports)
2. Test class name should be: {class_name}Test
3. Use proper JUnit 5 and Mockito patterns
4. Create tests for these specific methods: {[m['name'] for m in methods_in_chunk]}
5. Use mocked dependencies: 
{deps_formatted}

### Code Chunk (lines {first_chunk['start_line']}-{first_chunk['end_line']}):
```java
{first_chunk['code']}
```

### Methods to test in this chunk:
{chr(10).join([f"- {m['name']}()" for m in methods_in_chunk])}"""

        print("\nFirst 500 chars of chunk prompt:")
        print(chunk_prompt[:500])
        print(f"\nFull chunk prompt length: {len(chunk_prompt)} characters")
    else:
        print("No methods found in first chunk") 