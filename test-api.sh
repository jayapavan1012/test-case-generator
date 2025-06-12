#!/bin/bash

echo "🚀 Deepseek-Coder 6.7B Test Generator API Demo"
echo "================================================"
echo ""

BASE_URL="http://localhost:8081/api/deepseek"

echo "1. 📋 Testing API Status..."
curl -s "$BASE_URL/test" | jq '.'
echo ""

echo "2. 💓 Checking Health Status..."
curl -s "$BASE_URL/health" | jq '.'
echo ""

echo "3. 🖥️  Checking System Status..."
curl -s "$BASE_URL/system-status" | jq '.'
echo ""

echo "4. 🔧 Testing Model Initialization..."
curl -s -X POST "$BASE_URL/initialize" | jq '.'
echo ""

echo "5. 📝 Testing Test Generation (JSON API)..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } public int multiply(int a, int b) { return a * b; } }",
    "className": "Calculator"
  }' \
  "$BASE_URL/generate-tests" | jq '.'
echo ""

echo "6. 📝 Testing Test Generation (Simple Text API)..."
curl -s -X POST -H "Content-Type: text/plain" \
  -d "public class MathUtils { public static int fibonacci(int n) { if (n <= 1) return n; return fibonacci(n-1) + fibonacci(n-2); } }" \
  "$BASE_URL/generate" | jq '.'
echo ""

echo "7. 🧹 Testing Cache Clear..."
curl -s -X POST "$BASE_URL/clear-cache" | jq '.'
echo ""

echo "✅ API Demo Complete!"
echo ""
echo "📊 Summary:"
echo "- Model: Deepseek-Coder 6.7B-Instruct (Q4_K_M)"
echo "- Server: Distm1 (10.5.17.187)"
echo "- Optimization: 32GB RAM EC2"
echo "- Framework: JUnit 5"
echo "- Context Window: 8K tokens"
echo ""
echo "🔗 Key Endpoints:"
echo "- GET  /api/deepseek/test          - API status"
echo "- GET  /api/deepseek/health        - Health check"
echo "- POST /api/deepseek/initialize    - Initialize model"
echo "- POST /api/deepseek/generate-tests - Generate tests (JSON)"
echo "- POST /api/deepseek/generate      - Generate tests (Text)"
echo "- GET  /api/deepseek/system-status - System metrics"
echo "- POST /api/deepseek/clear-cache   - Clear cache" 