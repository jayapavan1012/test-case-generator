#!/bin/bash

echo "🧪 Testing Deepseek-Coder EC2 Server Connection"
echo "=============================================="
echo ""

EC2_SERVER="http://10.5.17.187:8080"

echo "1. 💓 Health Check..."
curl -s "$EC2_SERVER/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Server: {data.get(\"server\", \"Unknown\")}')
    print(f'✅ Model: {data.get(\"model\", \"Unknown\")}')
    print(f'✅ Status: {data.get(\"status\", \"Unknown\")}')
    print(f'✅ Model Loaded: {data.get(\"model_loaded\", \"Unknown\")}')
    sys_info = data.get('system_info', {})
    print(f'💾 Memory: {sys_info.get(\"used_memory_gb\", 0):.1f}GB / {sys_info.get(\"total_memory_gb\", 0):.1f}GB ({sys_info.get(\"memory_percent\", 0):.1f}% used)')
except:
    print('❌ Failed to parse health response')
" 2>/dev/null || echo "❌ Health check failed"

echo ""
echo "2. 🧪 Test Generation..."
curl -s -X POST "$EC2_SERVER/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } public int multiply(int a, int b) { return a * b; } }",
    "className": "Calculator"
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    response = data.get('response', '')
    gen_time = data.get('generation_time_seconds', 0)
    print(f'✅ Generation Time: {gen_time:.2f} seconds')
    print(f'✅ Generated Code Length: {len(response)} characters')
    print()
    print('📝 Generated Test Code Preview:')
    print('=' * 50)
    print(response[:500] + ('...' if len(response) > 500 else ''))
    print('=' * 50)
except Exception as e:
    print(f'❌ Failed to parse generation response: {e}')
" 2>/dev/null || echo "❌ Test generation failed"

echo ""
echo "3. 📊 System Status..."
curl -s "$EC2_SERVER/system-status" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'💻 Total RAM: {data.get(\"total_memory_gb\", 0):.1f}GB')
    print(f'💾 Available RAM: {data.get(\"available_memory_gb\", 0):.1f}GB')
    print(f'🖥️  CPU Usage: {data.get(\"cpu_percent\", 0):.1f}%')
    print(f'⚡ Memory Usage: {data.get(\"memory_percent\", 0):.1f}%')
except:
    print('❌ Failed to parse system status')
" 2>/dev/null || echo "❌ System status check failed"

echo ""
echo "✅ EC2 Deepseek-Coder Server Test Complete!"
echo ""
echo "🔗 Server Endpoints:"
echo "   Health:     $EC2_SERVER/health"
echo "   Generate:   $EC2_SERVER/generate"
echo "   Initialize: $EC2_SERVER/initialize-model"
echo "   Status:     $EC2_SERVER/system-status" 