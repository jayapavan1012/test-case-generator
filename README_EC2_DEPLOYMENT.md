# 🚀 EC2 Optimized CodeLlama Test Generator

## 📋 Overview

This is an **optimized version** of the CodeLlama 13B test generator specifically tuned for **EC2 instances with 32GB RAM**. The optimization provides significant performance improvements and better resource utilization.

## ⚡ Performance Improvements

| **Feature** | **Before** | **After** | **Improvement** |
|-------------|------------|-----------|-----------------|
| **CPU Threads** | 8 threads | 16 threads (CPU) / 8+GPU | **2x parallelism** |
| **Memory Utilization** | Basic | Optimized with monitoring | **Smart memory usage** |
| **Response Caching** | None | Hash-based caching | **Instant repeated requests** |
| **Batch Processing** | 256 | 512 (CPU) / 1024 (GPU) | **2-4x throughput** |
| **Memory Mapping** | Disabled | Enabled with mlock | **Faster model loading** |
| **Monitoring** | None | Real-time system stats | **Performance visibility** |

## 🛠️ Key Optimizations Applied

### 1. **Memory Optimization (32GB RAM)**
- **16 CPU threads** for maximum CPU utilization
- **Memory-mapped model loading** for faster startup
- **Memory locking** to prevent swapping
- **Real-time memory monitoring** and reporting

### 2. **GPU Support (Optional)**
- **Full GPU offloading** (32 layers) when available
- **Hybrid CPU+GPU** configuration
- **Automatic thread adjustment** based on GPU usage

### 3. **Caching System**
- **Hash-based result caching** for identical requests
- **Instant responses** for cached queries
- **Memory-efficient** cache management

### 4. **Enhanced Error Handling**
- **Graceful fallbacks** when model unavailable
- **Detailed error reporting** with memory stats
- **Robust JSON parsing** and validation

### 5. **Performance Monitoring**
- **Real-time memory usage** tracking
- **CPU utilization** monitoring  
- **Generation time** measurement
- **Cache hit rate** reporting

## 🔧 Installation & Deployment

### Option 1: Automated EC2 Deployment

1. **Use the deployment script:**
```bash
./deploy_to_ec2.sh your-ec2-host.com ~/.ssh/your-key.pem false
```

2. **SSH to your EC2 instance:**
```bash
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-host.com
```

3. **Start the optimized server:**
```bash
cd test-generator && ./start_server.sh
```

### Option 2: Manual EC2 Setup

1. **Copy the optimized script:**
```bash
scp -i ~/.ssh/your-key.pem python/codellama_test_generator.py ubuntu@your-ec2:/home/ubuntu/
```

2. **Install dependencies:**
```bash
pip3 install --user flask llama-cpp-python psutil
```

3. **Start the server:**
```bash
python3 codellama_test_generator.py --port 8082 --model-path /path/to/model.gguf
```

### Option 3: GPU-Enabled Deployment

```bash
python3 codellama_test_generator.py --port 8082 --use-gpu --model-path /path/to/model.gguf
```

## 📡 API Endpoints

### **Health & Monitoring**
- `GET /health` - Server health with optimization info
- `GET /system-status` - Real-time memory and CPU usage
- `GET /model-info` - Detailed model and capability info

### **Model Management**
- `POST /initialize-model` - Load model with GPU option
```json
{
  "model_path": "/path/to/model.gguf",
  "use_gpu": false
}
```

### **Test Generation**
- `POST /generate` - Generate JUnit tests with monitoring
```json
{
  "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
  "className": "Calculator"
}
```

### **Cache Management**
- `POST /clear-cache` - Clear the result cache

## 📊 Performance Monitoring

### **Real-Time System Stats**
```bash
curl http://your-ec2:8082/system-status
```

**Response:**
```json
{
  "total_memory_gb": 32.0,
  "available_memory_gb": 24.5,
  "used_memory_gb": 7.5,
  "memory_percent": 23.4,
  "cpu_percent": 15.2
}
```

### **Generation Performance**
```bash
curl -X POST http://your-ec2:8082/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "public class Test {}", "className": "Test"}'
```

**Response includes:**
```json
{
  "response": "generated JUnit tests...",
  "generation_time_seconds": 2.34,
  "cache_size": 5,
  "memory_info": { "available_memory_gb": 24.2 }
}
```

## 🎯 Configuration Options

### **CPU Optimization (Recommended for most EC2 instances)**
```bash
python3 codellama_test_generator.py \
  --port 8082 \
  --host 0.0.0.0 \
  --model-path /path/to/model.gguf
```

### **GPU Acceleration (For GPU-enabled EC2 instances)**
```bash
python3 codellama_test_generator.py \
  --port 8082 \
  --host 0.0.0.0 \
  --model-path /path/to/model.gguf \
  --use-gpu
```

## 🔍 Troubleshooting

### **Memory Issues**
- Monitor with: `curl http://localhost:8082/system-status`
- Ensure 8GB+ available before model loading
- Use swap if needed: `sudo swapon /swapfile`

### **Performance Issues**
- Check CPU usage: `htop`
- Monitor generation times in response
- Clear cache: `curl -X POST http://localhost:8082/clear-cache`

### **Model Loading Issues**
- Verify model path exists
- Check permissions: `ls -la /path/to/model.gguf`
- Monitor logs: `tail -f logs/codellama_server.log`

## 📈 Expected Performance

### **32GB EC2 Instance (CPU-only)**
- **Model Loading:** 30-60 seconds
- **Test Generation:** 10-45 seconds per request  
- **Cached Responses:** 0.1-0.5 seconds
- **Memory Usage:** 6-8GB for model + 2-4GB overhead

### **GPU-Enabled EC2 Instance**
- **Model Loading:** 20-40 seconds
- **Test Generation:** 3-15 seconds per request
- **Cached Responses:** 0.1-0.2 seconds  
- **Memory Usage:** 4-6GB GPU VRAM + 2-3GB RAM

## 🏆 Production Best Practices

1. **Enable result caching** for repeated code patterns
2. **Monitor memory usage** regularly via `/system-status`
3. **Use GPU acceleration** when available for better performance
4. **Set up log rotation** for long-running instances
5. **Configure security groups** to restrict access to port 8082
6. **Use process managers** like systemd for automatic restart

## 🚀 Ready for Production

The optimized CodeLlama generator is now **production-ready** with:

✅ **Sub-60-second generation times**  
✅ **32GB RAM optimization**  
✅ **Real-time monitoring**  
✅ **Robust error handling**  
✅ **GPU acceleration support**  
✅ **Result caching**  
✅ **Memory efficiency**  

Deploy to your EC2 instance and enjoy **high-performance JUnit test generation**! 