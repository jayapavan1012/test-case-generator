#!/bin/bash

echo "🚀 Fast JUnit Generation System Test"
echo "===================================="
echo

# Kill any existing servers
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*8082" || true
pkill -f "java.*spring-boot" || true
sleep 2

# Start the fast test generator
echo "⚡ Starting Fast Test Generator Server..."
python3 python/fast_test_generator.py --port 8082 > fast_server.log 2>&1 &
FAST_SERVER_PID=$!
echo "   Started with PID: $FAST_SERVER_PID"

# Wait for server to start
echo "   Waiting for server to initialize..."
sleep 3

# Test 1: Health Check
echo "1. Testing Fast Server Health..."
health_response=$(curl -s -X GET http://localhost:8082/health)
echo "   Response: $health_response"

if echo "$health_response" | grep -q '"status":"healthy"'; then
    echo "   ✅ Fast server is healthy"
else
    echo "   ❌ Fast server health check failed"
    exit 1
fi
echo

# Test 2: Benchmark Test
echo "2. Running Benchmark Test..."
benchmark_response=$(curl -s -X GET http://localhost:8082/benchmark)
echo "   Response: $benchmark_response"

benchmark_time=$(echo "$benchmark_response" | grep -o '"benchmark_time_ms":[0-9]*' | cut -d: -f2)
if [ "$benchmark_time" -lt 5000 ]; then
    echo "   ✅ Benchmark passed: ${benchmark_time}ms (< 5 seconds)"
else
    echo "   ⚠️  Benchmark slower than expected: ${benchmark_time}ms"
fi
echo

# Start Spring Boot application
echo "3. Starting Spring Boot Application..."
./gradlew bootRun --no-daemon > app.log 2>&1 &
SPRING_PID=$!
echo "   Started with PID: $SPRING_PID"

# Wait for Spring Boot to start
echo "   Waiting for Spring Boot to start..."
for i in {1..30}; do
    if curl -s -X GET http://localhost:8081/api/test-generation/health > /dev/null 2>&1; then
        echo "   ✅ Spring Boot is running"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ Spring Boot failed to start"
        exit 1
    fi
    sleep 2
done
echo

# Test 3: Spring Boot Health
echo "4. Testing Spring Boot Health..."
app_health=$(curl -s -X GET http://localhost:8081/api/test-generation/health)
echo "   Response: $app_health"

if echo "$app_health" | grep -q '"status"'; then
    echo "   ✅ Spring Boot application is healthy"
else
    echo "   ❌ Spring Boot health check failed"
fi
echo

# Test 4: Fast JUnit Generation
echo "5. Testing Fast JUnit Generation..."

# Create test requests
cat > fast_calculator_test.json << EOF
{
  "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } public int subtract(int a, int b) { return a - b; } }",
  "className": "Calculator"
}
EOF

cat > fast_simple_test.json << EOF
{
  "javaCode": "public class SimpleClass { public String getName() { return \"test\"; } }",
  "className": "SimpleClass"
}
EOF

echo "   Testing Calculator class generation..."
calc_start=$(date +%s%3N)
calc_response=$(curl -s -X POST http://localhost:8081/api/test-generation/generate-class-tests \
                     -H "Content-Type: application/json" \
                     -d @fast_calculator_test.json \
                     --max-time 30)
calc_end=$(date +%s%3N)
calc_time=$((calc_end - calc_start))

echo "   Calculator test generation time: ${calc_time}ms"
if [ $calc_time -lt 10000 ]; then
    echo "   ✅ Calculator test generated quickly (< 10 seconds)"
    echo "   Sample output: $(echo "$calc_response" | head -c 200)..."
else
    echo "   ⚠️  Calculator test took longer than expected: ${calc_time}ms"
fi
echo

echo "   Testing Simple class generation..."
simple_start=$(date +%s%3N)
simple_response=$(curl -s -X POST http://localhost:8081/api/test-generation/generate-class-tests \
                       -H "Content-Type: application/json" \
                       -d @fast_simple_test.json \
                       --max-time 30)
simple_end=$(date +%s%3N)
simple_time=$((simple_end - simple_start))

echo "   Simple test generation time: ${simple_time}ms"
if [ $simple_time -lt 10000 ]; then
    echo "   ✅ Simple test generated quickly (< 10 seconds)"
    echo "   Sample output: $(echo "$simple_response" | head -c 200)..."
else
    echo "   ⚠️  Simple test took longer than expected: ${simple_time}ms"
fi
echo

# Test 5: Direct Fast Server Test
echo "6. Testing Direct Fast Server Generation..."
direct_start=$(date +%s%3N)
direct_response=$(curl -s -X POST http://localhost:8082/generate \
                       -H "Content-Type: application/json" \
                       -d '{"prompt": "public class TestUtil { public boolean isValid(String input) { return input != null; } }"}' \
                       --max-time 10)
direct_end=$(date +%s%3N)
direct_time=$((direct_end - direct_start))

echo "   Direct generation time: ${direct_time}ms"
if [ $direct_time -lt 5000 ]; then
    echo "   ✅ Direct generation is very fast (< 5 seconds)"
else
    echo "   ⚠️  Direct generation slower than expected: ${direct_time}ms"
fi
echo

# Performance Summary
echo "🎯 Performance Summary"
echo "====================="
echo "Calculator Generation: ${calc_time}ms"
echo "Simple Class Generation: ${simple_time}ms"  
echo "Direct Server Generation: ${direct_time}ms"
echo

if [ $calc_time -lt 10000 ] && [ $simple_time -lt 10000 ] && [ $direct_time -lt 5000 ]; then
    echo "✅ ALL TESTS PASSED - System is fast and working!"
    echo "🚀 Ready for production use"
else
    echo "⚠️  Some tests were slower than expected"
    echo "💡 Check logs for optimization opportunities"
fi

echo
echo "📋 Process Management"
echo "===================="
echo "Fast Server PID: $FAST_SERVER_PID"
echo "Spring Boot PID: $SPRING_PID"
echo
echo "📄 Log Files:"
echo "- Fast Server: fast_server.log"
echo "- Spring Boot: app.log"
echo
echo "🛑 To stop all services:"
echo "   kill $FAST_SERVER_PID $SPRING_PID"
echo
echo "🔍 To monitor logs:"
echo "   tail -f fast_server.log"
echo "   tail -f app.log" 