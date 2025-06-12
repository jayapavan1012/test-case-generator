# 🚀 Deepseek-Coder 6.7B-Instruct Deployment Guide
## EC2 Distm1 (10.5.17.187) - Complete Setup

### 🎯 **Overview**
This guide sets up **Deepseek-Coder 6.7B-Instruct (Q4_K_M)** on your EC2 instance with optimized Spring Boot integration.

**Model Advantages:**
- ✅ **Smaller & Faster**: 6.7B vs 13B parameters
- ✅ **Code-Specialized**: Specifically trained for code generation
- ✅ **Memory Efficient**: ~4GB RAM usage (vs 8-12GB for CodeLlama 13B)
- ✅ **Better for 32GB EC2**: Leaves more memory for other processes

---

## 📋 **Step 1: Connect to Distm1**

```bash
ssh adminuser@10.5.17.187
# Password: 92<ae8JEzi/B
```

---

## 🔧 **Step 2: System Setup**

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3 python3-pip wget curl htop

# Install Python packages (optimized for Deepseek-Coder)
pip3 install --user flask llama-cpp-python psutil

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## 📥 **Step 3: Download Deepseek-Coder Model**

```bash
# Create model directory
mkdir -p /home/adminuser/models
cd /home/adminuser/models

# Download Deepseek-Coder 6.7B-Instruct (Q4_K_M) - ~4.2GB
# Option 1: Direct download (if available)
wget -O deepseek-coder-6.7b-instruct.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf"

# Option 2: Using huggingface-hub
pip3 install --user huggingface-hub
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='TheBloke/deepseek-coder-6.7B-instruct-GGUF',
    filename='deepseek-coder-6.7b-instruct.Q4_K_M.gguf',
    local_dir='/home/adminuser/models',
    local_dir_use_symlinks=False
)
"

# Verify download
ls -lh /home/adminuser/models/
```

---

## 🐍 **Step 4: Deploy Deepseek-Coder Server**

### Create the Python server:
```bash
nano /home/adminuser/deepseek_coder_server.py
```

**Copy the entire `deepseek_coder_server.py` content from your local file.**

### Make executable and create logs:
```bash
chmod +x /home/adminuser/deepseek_coder_server.py
mkdir -p /home/adminuser/logs
```

---

## 🚀 **Step 5: Start Deepseek-Coder Server**

### Start in CPU mode (recommended for stability):
```bash
nohup python3 /home/adminuser/deepseek_coder_server.py \
  --port 8082 \
  --host 0.0.0.0 \
  --model-path /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf \
  > /home/adminuser/logs/deepseek-coder.log 2>&1 &
```

### Or start with GPU acceleration (if available):
```bash
nohup python3 /home/adminuser/deepseek_coder_server.py \
  --port 8082 \
  --host 0.0.0.0 \
  --model-path /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf \
  --use-gpu \
  > /home/adminuser/logs/deepseek-coder.log 2>&1 &
```

---

## 🧪 **Step 6: Test Deepseek-Coder Server**

### Check server health:
```bash
curl http://localhost:8082/health | jq
```

### Expected response:
```json
{
  "status": "healthy",
  "server": "Distm1 (10.5.17.187)",
  "model": "Deepseek-Coder 6.7B-Instruct (Q4_K_M)",
  "model_loaded": true,
  "specialization": "Java JUnit 5 test generation",
  "system_info": {
    "total_memory_gb": 32.0,
    "available_memory_gb": 28.5,
    "memory_percent": 10.9,
    "cpu_percent": 5.2
  }
}
```

### Test generation:
```bash
curl -X POST http://localhost:8082/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator"
  }' | jq
```

---

## ☕ **Step 7: Update Spring Boot Application**

### Build and run your Spring Boot app:
```bash
# On your local machine (where the Spring Boot app is)
./gradlew clean build

# Run the application
./gradlew bootRun
```

### Test Spring Boot integration:
```bash
# Test the new Deepseek-Coder endpoints
curl http://localhost:8081/api/deepseek/health | jq

# Test generation via Spring Boot
curl -X POST http://localhost:8081/api/deepseek/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator"
  }' | jq
```

---

## 📊 **Step 8: Monitor Performance**

### Real-time logs:
```bash
tail -f /home/adminuser/logs/deepseek-coder.log
```

### System resources:
```bash
# Check memory usage
curl http://10.5.17.187:8082/system-status | jq

# Check processes
ps aux | grep deepseek

# System monitoring
htop
```

---

## 🔧 **Step 9: Production Configuration**

### Create systemd service (optional):
```bash
sudo nano /etc/systemd/system/deepseek-coder.service
```

```ini
[Unit]
Description=Deepseek-Coder 6.7B Test Generator
After=network.target

[Service]
Type=simple
User=adminuser
WorkingDirectory=/home/adminuser
ExecStart=/usr/bin/python3 /home/adminuser/deepseek_coder_server.py --port 8082 --host 0.0.0.0 --model-path /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable deepseek-coder
sudo systemctl start deepseek-coder
sudo systemctl status deepseek-coder
```

---

## 🌐 **Step 10: API Endpoints Reference**

### Deepseek-Coder Server (Port 8082):
- **Health**: `GET http://10.5.17.187:8082/health`
- **Generate**: `POST http://10.5.17.187:8082/generate`
- **System Status**: `GET http://10.5.17.187:8082/system-status`
- **Initialize**: `POST http://10.5.17.187:8082/initialize-model`
- **Clear Cache**: `POST http://10.5.17.187:8082/clear-cache`

### Spring Boot API (Port 8081):
- **Health**: `GET http://localhost:8081/api/deepseek/health`
- **Generate Tests**: `POST http://localhost:8081/api/deepseek/generate-tests`
- **System Status**: `GET http://localhost:8081/api/deepseek/system-status`
- **Initialize**: `POST http://localhost:8081/api/deepseek/initialize`
- **Test Endpoint**: `GET http://localhost:8081/api/deepseek/test`

---

## 🚨 **Troubleshooting**

### If model fails to load:
```bash
# Check available memory
free -h

# Check model file
ls -lh /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf

# Restart with more verbose logging
python3 /home/adminuser/deepseek_coder_server.py --port 8082 --host 0.0.0.0 --model-path /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf
```

### If generation is slow:
```bash
# Check system resources
curl http://10.5.17.187:8082/system-status

# Restart with CPU optimization
pkill -f deepseek
nohup python3 /home/adminuser/deepseek_coder_server.py --port 8082 --host 0.0.0.0 > /home/adminuser/logs/deepseek-coder.log 2>&1 &
```

### Common issues:
1. **JSON parsing errors**: Fixed in the new server implementation
2. **Memory issues**: Deepseek-Coder 6.7B uses only ~4GB vs 8-12GB for CodeLlama 13B
3. **Timeout errors**: Reduced timeout to 120 seconds (vs 180 for larger models)

---

## ✅ **Expected Performance**

### Generation Times:
- **Simple classes**: 5-15 seconds
- **Complex classes**: 15-30 seconds  
- **Large classes**: 30-45 seconds

### Memory Usage:
- **Model**: ~4GB RAM
- **Available for OS**: ~28GB RAM
- **CPU Usage**: 60-80% during generation

### Quality Expectations:
- ✅ **JUnit 5** annotations and imports
- ✅ **Comprehensive test coverage** for all public methods
- ✅ **Edge cases and boundary conditions**
- ✅ **Proper assertions** (assertEquals, assertTrue, assertThrows)
- ✅ **Clean, readable test code**

---

## 🎉 **Success Verification**

Once everything is running, you should see:

```bash
# Server health
curl http://10.5.17.187:8082/health
# Returns: {"status": "healthy", "model": "Deepseek-Coder 6.7B-Instruct"}

# Spring Boot health  
curl http://localhost:8081/api/deepseek/health
# Returns: {"status": "healthy", "model_ready": true}

# Working generation
curl -X POST http://localhost:8081/api/deepseek/generate-tests \
  -H "Content-Type: application/json" \
  -d '{"javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }", "className": "Calculator"}'
# Returns: Complete JUnit 5 test class
```

🚀 **Your Deepseek-Coder 6.7B-Instruct test generator is now ready!** 