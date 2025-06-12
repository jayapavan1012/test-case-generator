# 🚀 DEEPSEEK-CODER-V2:16B INTEGRATION GUIDE

## Architecture Overview

```
┌─────────────────┐    HTTP/REST     ┌─────────────────┐    HTTP/REST     ┌─────────────────┐
│   Spring Boot   │ ────────────────► │  Python Server  │ ────────────────► │     Ollama      │
│   Application   │                  │(10.5.17.187:9092)│                 │  (Port 11434)   │
│   (Port 8081)   │                  │                 │                  │                 │
│                 │                  │ Multi-Model:    │                  │ Deepseek-V2:16b │
│ REST Endpoints: │                  │ • Deepseek-V2   │                  │                 │
│ /api/deepseek/* │                  │ • Deepseek-6B   │                  │                 │
│                 │                  │ • Demo Mode     │                  │                 │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
```

## 🏗️ Setup Prerequisites

### 1. Ollama with Deepseek-V2:16b
```bash
# Install and run Deepseek-V2:16b on your production server
ollama run deepseek-coder-v2:16b
```

### 2. Python Server (10.5.17.187:9092)
```bash
# Start the multi-model Python server on production server
python3 deepseek_coder_server.py --port 9092 --use-gpu
```

### 3. Spring Boot Application (Port 8081)
```bash
# Build and run Spring Boot application locally
./gradlew bootRun
```

## 🧪 Testing Your Integration

### Quick Test (Manual)
```bash
# 1. Test Python server health
curl http://10.5.17.187:9092/health

# 2. Test Spring Boot health
curl http://localhost:8081/api/deepseek/health

# 3. Test end-to-end generation
curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "auto"
  }'

# 4. Test direct Python server (same as your curl)
curl --location 'http://10.5.17.187:9092/generate' \
  --header 'Content-Type: application/json' \
  -d '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "deepseek-v2"
  }'
```

### Comprehensive Test Suite
```bash
# Run the automated integration tests
./test_v2_integration.sh
```

## 🤖 Available Models

### Model Selection Options:
- **`"auto"`** - Automatically selects best available (V2 → 6B → Demo)
- **`"deepseek-v2"`** - Force Deepseek-Coder-V2:16b (Ollama)
- **`"deepseek-6b"`** - Force Deepseek-Coder 6.7B (llama-cpp)
- **`"demo"`** - Use demo test generation

### Performance Expectations:
- **Deepseek-V2:16b**: 15-45 seconds (HIGH QUALITY tests)
- **Deepseek-6B**: 3-15 seconds (GOOD QUALITY tests)
- **Demo Mode**: < 1 second (TEMPLATE tests)

## 📡 API Endpoints

### Spring Boot Endpoints (localhost:8081)

#### Health & Status
- `GET /api/deepseek/health` - Overall health check
- `GET /api/deepseek/models-status` - Models availability
- `GET /api/deepseek/system-status` - System resources
- `POST /api/deepseek/test-deepseek-v2` - Test V2 connectivity

#### Test Generation
- `POST /api/deepseek/generate-tests` - Legacy generation (auto model)
- `POST /api/deepseek/generate-tests-v2` - **NEW** V2 generation with model selection

#### Cache Management
- `POST /api/deepseek/clear-cache` - Clear generation cache
- `POST /api/deepseek/initialize` - Initialize models

### Python Server Endpoints (10.5.17.187:9092)

#### Health & Status
- `GET /health` - Server health
- `GET /models/status` - Models status
- `GET /system-status` - System info

#### Test Generation
- `POST /generate` - Generate with model selection **(Your Current API)**
- `POST /test-deepseek-v2` - Test V2 model
- `POST /quick-test` - Test 6B model

## 🎯 Example Requests

### 1. Direct Python Server (Your Current Setup)
```bash
curl --location 'http://10.5.17.187:9092/generate' \
  --header 'Content-Type: application/json' \
  -d '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "deepseek-v2"
  }'
```

### 2. Spring Boot V2 Endpoint (Auto Model Selection)
```json
POST /api/deepseek/generate-tests-v2
{
  "javaCode": "public class BankAccount { private double balance; public void deposit(double amount) { balance += amount; } public double getBalance() { return balance; } }",
  "className": "BankAccount",
  "model": "auto"
}
```

### 3. Spring Boot V2 Endpoint (Force Deepseek-V2)
```json
POST /api/deepseek/generate-tests-v2
{
  "javaCode": "public class Calculator { public int multiply(int a, int b) { return a * b; } }",
  "className": "Calculator", 
  "model": "deepseek-v2"
}
```

### 4. Spring Boot V2 Endpoint (Fallback to 6B)
```json
POST /api/deepseek/generate-tests-v2
{
  "javaCode": "public class StringUtils { public boolean isEmpty(String str) { return str == null || str.length() == 0; } }",
  "className": "StringUtils",
  "model": "deepseek-6b"
}
```

## 📊 Response Format

### Successful Response
```json
{
  "generatedTests": "import org.junit.jupiter.api.Test;\n...",
  "className": "Calculator",
  "generationTimeMs": 12500,
  "modelRequested": "auto",
  "modelUsed": "Deepseek-Coder-V2:16b",
  "server": "Production Server (10.5.17.187:9092)",
  "testFramework": "JUnit 5",
  "version": "Deepseek-V2 Multi-Model"
}
```

### Error Response
```json
{
  "error": "Failed to generate tests: Connection timeout",
  "server": "Production Server (10.5.17.187:9092)"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Ollama Not Running (Production Server)
```bash
# Check Ollama status on production server
curl http://10.5.17.187:11434/api/tags

# SSH to production server and start Ollama if needed
ssh production-server
ollama serve
ollama run deepseek-coder-v2:16b
```

#### 2. Python Server Connection Issues
```bash
# Check Python server
curl http://10.5.17.187:9092/health

# SSH to production server and restart with verbose logging
ssh production-server
python3 deepseek_coder_server.py --port 9092 --use-gpu --verbose
```

#### 3. Spring Boot Connection Issues
```bash
# Check Spring Boot logs locally
tail -f logs/test-generator.log

# Check configuration
grep "deepseek.coder.server.url" src/main/resources/application.properties
# Should show: deepseek.coder.server.url=http://10.5.17.187:9092
```

#### 4. Model Loading Issues
```bash
# Check available models on production server
curl http://10.5.17.187:9092/models/status

# Force model initialization on production server
curl -X POST http://10.5.17.187:9092/initialize-model \
  -H "Content-Type: application/json" \
  -d '{"use_gpu": true}'
```

## 🚀 Production Deployment

### Configuration Checklist
- [ ] Ollama running with Deepseek-V2:16b on production server
- [ ] Python server on production server (10.5.17.187:9092)
- [ ] Spring Boot on local machine (localhost:8081)
- [ ] All health checks passing
- [ ] Integration tests passing (>90%)
- [ ] GPU memory sufficient (>20GB free) on production server
- [ ] Network connectivity between local and production server

### Monitoring
```bash
# Monitor system resources (local Spring Boot)
curl http://localhost:8081/api/deepseek/system-status

# Monitor generation performance (production server)
curl http://10.5.17.187:9092/models/status

# Check logs (local)
tail -f logs/test-generator.log
tail -f integration_test.log
```

## ✅ Integration Verification

Run this complete verification sequence:

```bash
# 1. Verify production server is running
curl http://10.5.17.187:9092/health

# 2. Start Spring Boot locally
./gradlew bootRun &

# 3. Wait for startup (10 seconds)
sleep 10

# 4. Run comprehensive tests
./test_v2_integration.sh

# 5. Check results
echo "Integration Status: $(cat integration_test.log | grep -c 'PASS')/16 tests passed"
```

### Manual Test Your Exact Setup:
```bash
# Test your exact curl command
curl --location 'http://10.5.17.187:9092/generate' \
  --header 'Content-Type: application/json' \
  -d '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "deepseek-v2"
  }'

# Test through Spring Boot integration
curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "deepseek-v2"
  }'
```

If both tests work, your **Deepseek-Coder-V2:16b** integration is ready for production! 🎉 