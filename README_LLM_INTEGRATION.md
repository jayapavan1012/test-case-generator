# LLM Integration for Test Case Generation

This document explains the Local Language Model (LLM) integration for automated JUnit test case generation using Llama 2.

## Overview

The LLM integration consists of:
- **Java Spring Boot Service**: Handles test generation requests and manages the Python LLM server
- **Python LLM Server**: Serves the local Llama model using HuggingFace transformers
- **Caching Layer**: Improves performance by caching generated tests
- **REST API**: Provides endpoints for test generation

## Architecture

```
Java Application ←→ Python LLM Server ←→ Local Llama Model
      ↓
   Cache Layer
      ↓
   REST API Endpoints
```

## Setup Instructions

### 1. Python Environment Setup

First, set up the Python environment for the LLM server:

```bash
# Create virtual environment
python3 -m venv llm_env
source llm_env/bin/activate  # On Windows: llm_env\Scripts\activate

# Install dependencies
pip install -r python/requirements.txt
```

### 2. Model Download

Download the Llama 2 model (this requires HuggingFace account and acceptance of model license):

```bash
# Login to HuggingFace (requires account)
huggingface-cli login

# The model will be automatically downloaded when first used
# Or pre-download with:
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-chat-hf'); AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-chat-hf')"
```

### 3. Java Application Setup

Build and run the Java application:

```bash
# Build the project
./gradlew build

# Run the application
./gradlew bootRun
```

## Configuration

### Application Properties

The LLM service can be configured via `application.properties`:

```properties
# LLM Configuration
llm.model-name=meta-llama/Llama-2-7b-chat-hf
llm.server-url=http://localhost:8080
llm.server-port=8080
llm.max-tokens=2048
llm.temperature=0.7
```

### Python Server Options

The Python server supports various options:

```bash
python3 python/llm_server.py --help
```

Options:
- `--model`: Model name or path (default: meta-llama/Llama-2-7b-chat-hf)
- `--port`: Server port (default: 8080)
- `--host`: Server host (default: 127.0.0.1)
- `--no-quantization`: Disable model quantization

## Usage

### Starting the Services

1. **Start Python LLM Server** (automatically started by Java app):
```bash
python3 python/llm_server.py --model meta-llama/Llama-2-7b-chat-hf --port 8080
```

2. **Start Java Application**:
```bash
./gradlew bootRun
```

### API Endpoints

#### Health Check
```bash
GET /api/test-generation/health
```

#### Generate Class Tests
```bash
POST /api/test-generation/generate-class-tests
Content-Type: application/json

{
  "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
  "className": "Calculator",
  "existingTestStyle": "// Optional existing test style"
}
```

#### Generate Method Tests
```bash
POST /api/test-generation/generate-method-tests
Content-Type: application/json

{
  "methodSignature": "public int add(int a, int b)",
  "methodBody": "return a + b;",
  "className": "Calculator"
}
```

#### Analyze Test Patterns
```bash
POST /api/test-generation/analyze-test-patterns
Content-Type: application/json

{
  "existingTests": [
    "public class TestExample { @Test public void testMethod() { ... } }"
  ]
}
```

### Example Usage

```bash
# Check if LLM service is ready
curl -X GET http://localhost:8081/api/test-generation/health

# Generate tests for a simple class
curl -X POST http://localhost:8081/api/test-generation/generate-class-tests \
  -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } public int multiply(int a, int b) { return a * b; } }",
    "className": "Calculator"
  }'
```

## Features

### Implemented Features

1. **Local Llama Model Integration**: Uses local Llama 2 model for privacy and cost efficiency
2. **Caching**: Caches generated tests to improve performance
3. **Context-Aware Generation**: Considers existing test styles
4. **Multiple Generation Modes**: Class-level and method-level test generation
5. **Pattern Analysis**: Analyzes existing test patterns
6. **REST API**: Easy integration with other tools

### Prompt Engineering

The service uses specialized prompts for different types of test generation:

- **Class Test Generation**: Comprehensive test suite generation
- **Method Test Generation**: Focused method testing
- **Style Analysis**: Pattern extraction from existing tests

## Performance Considerations

### Model Optimization

- **Quantization**: 4-bit quantization for better performance
- **GPU Support**: Automatic GPU detection and usage
- **Memory Management**: Efficient memory usage with caching

### Caching Strategy

- **Response Caching**: Generated tests are cached based on input hash
- **Configurable TTL**: Cache expiration can be configured
- **Memory Limits**: Configurable cache size limits

## Troubleshooting

### Common Issues

1. **Model Loading Errors**:
   - Ensure HuggingFace login is complete
   - Check model license acceptance
   - Verify sufficient disk space and RAM

2. **Connection Errors**:
   - Check if Python server is running on correct port
   - Verify firewall settings
   - Check application.properties configuration

3. **Memory Issues**:
   - Reduce model quantization
   - Adjust cache settings
   - Use smaller model variant

### Logs

Check logs for debugging:
- Java logs: `logs/test-generator.log`
- Python server logs: Console output

## System Requirements

### Minimum Requirements
- **RAM**: 8GB (16GB recommended)
- **Storage**: 15GB free space
- **Python**: 3.8+
- **Java**: 17+

### Recommended Requirements
- **RAM**: 16GB+ 
- **GPU**: NVIDIA GPU with 6GB+ VRAM (optional but recommended)
- **Storage**: 20GB+ free space

## Security Considerations

- **Local Processing**: All code analysis happens locally
- **No Data Transmission**: Code never leaves your system
- **Access Control**: Configure appropriate network access controls

## Future Enhancements

- **Code Coverage Analysis**: Integration with JaCoCo
- **Multiple Model Support**: Support for different LLM models
- **Batch Processing**: Process multiple files simultaneously
- **IDE Integration**: Direct integration with popular IDEs 