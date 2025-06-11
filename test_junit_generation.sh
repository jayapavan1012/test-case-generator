#!/bin/bash

echo "🧪 JUnit Generation System Test Script"
echo "======================================="
echo

# Test 1: Check CodeLlama Server Health
echo "1. Testing CodeLlama Server Health..."
health_response=$(curl -s -X GET http://10.5.17.187:8082/health)
echo "   Response: $health_response"

if echo "$health_response" | grep -q '"model_loaded":true'; then
    echo "   ✅ CodeLlama server is healthy and model is loaded"
else
    echo "   ❌ CodeLlama server health check failed"
    exit 1
fi
echo

# Test 2: Check Spring Boot Application Health
echo "2. Testing Spring Boot Application Health..."
app_health=$(curl -s -X GET http://localhost:8081/api/test-generation/health)
echo "   Response: $app_health"

if echo "$app_health" | grep -q '"modelReady":true'; then
    echo "   ✅ Spring Boot application is healthy and ready"
else
    echo "   ❌ Spring Boot application health check failed"
    exit 1
fi
echo

# Test 3: Test model initialization endpoint
echo "3. Testing Model Initialization..."
init_response=$(curl -s -X POST http://localhost:8081/api/test-generation/initialize-model)
echo "   Response: $init_response"
echo

# Test 4: Test model status endpoint
echo "4. Testing Model Status..."
status_response=$(curl -s -X GET http://localhost:8081/api/test-generation/model-status)
echo "   Response: $status_response"
echo

# Test 5: Start test generation in background and monitor
echo "5. Starting JUnit Test Generation (Background)..."
echo "   This will run in the background - monitor with: tail -f junit_test_result.log"

# Create a simple test request
cat > minimal_test.json << EOF
{
  "javaCode": "public class Test { public int add(int a, int b) { return a + b; } }",
  "className": "Test"
}
EOF

# Start the test generation in background
{
    echo "$(date): Starting test generation..."
    curl -X POST http://localhost:8081/api/test-generation/generate-class-tests \
         -H "Content-Type: application/json" \
         -d @minimal_test.json \
         --max-time 600 \
         2>&1
    echo "$(date): Test generation completed"
} > junit_test_result.log 2>&1 &

echo "   Test generation started in background (PID: $!)"
echo "   Monitor progress with: tail -f junit_test_result.log"
echo "   Check completion with: ps aux | grep curl"
echo

echo "🎯 System Verification Complete!"
echo "================================"
echo "✅ All health checks passed"
echo "🚀 Test generation running in background"
echo ""
echo "📋 Next Steps:"
echo "1. Monitor: tail -f junit_test_result.log"
echo "2. Wait 5-10 minutes for CodeLlama to generate response"
echo "3. Check result in junit_test_result.log"
echo ""
echo "💡 Note: CodeLlama 13B on CPU is slow but powerful!"
echo "   First generation may take 5-10 minutes"
echo "   Subsequent requests should be faster"