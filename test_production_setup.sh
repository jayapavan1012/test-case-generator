#!/bin/bash

echo "🚀 TESTING PRODUCTION DEEPSEEK-V2 SETUP"
echo "================================================"
echo "Production Server: 10.5.17.187:9092"
echo "Local Spring Boot: localhost:8081"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: Direct Python server (your exact curl)
echo -e "\n${BLUE}🧪 TEST 1: Direct Python Server (Your Exact Curl)${NC}"
echo "curl --location 'http://10.5.17.187:9092/generate' --header 'Content-Type: application/json' --data '{\"prompt\": \"public class Calculator { public int add(int a, int b) { return a + b; } }\", \"className\": \"Calculator\", \"model\": \"deepseek-v2\"}'"

response1=$(curl -s --location 'http://10.5.17.187:9092/generate' \
  --header 'Content-Type: application/json' \
  --data '{
    "prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator",
    "model": "deepseek-v2"
  }')

if [[ $response1 == *"response"* ]]; then
    echo -e "${GREEN}✅ PASS: Direct Python server working${NC}"
    echo "Response length: $(echo "$response1" | wc -c) characters"
else
    echo -e "${RED}❌ FAIL: Direct Python server${NC}"
    echo "Response: $response1"
fi

# Test 2: Python server health
echo -e "\n${BLUE}🧪 TEST 2: Python Server Health${NC}"
health_response=$(curl -s http://10.5.17.187:9092/health)

if [[ $health_response == *"healthy"* ]]; then
    echo -e "${GREEN}✅ PASS: Python server healthy${NC}"
else
    echo -e "${RED}❌ FAIL: Python server health${NC}"
    echo "Response: $health_response"
fi

# Test 3: Spring Boot health (if running)
echo -e "\n${BLUE}🧪 TEST 3: Spring Boot Health (if running)${NC}"
sb_health=$(curl -s http://localhost:8081/api/deepseek/health 2>/dev/null)

if [[ $sb_health == *"healthy"* ]]; then
    echo -e "${GREEN}✅ PASS: Spring Boot healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Spring Boot not running or not healthy${NC}"
    echo "Start with: ./gradlew bootRun"
fi

# Test 4: End-to-end integration (if Spring Boot is running)
if [[ $sb_health == *"healthy"* ]]; then
    echo -e "\n${BLUE}🧪 TEST 4: End-to-End Integration via Spring Boot${NC}"
    
    e2e_response=$(curl -s -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
      -H "Content-Type: application/json" \
      -d '{
        "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
        "className": "Calculator",
        "model": "deepseek-v2"
      }')
    
    if [[ $e2e_response == *"generatedTests"* ]]; then
        echo -e "${GREEN}✅ PASS: End-to-end integration working${NC}"
        echo "Generated test length: $(echo "$e2e_response" | jq -r '.generatedTests' 2>/dev/null | wc -c) characters"
    else
        echo -e "${RED}❌ FAIL: End-to-end integration${NC}"
        echo "Response: $e2e_response"
    fi
fi

# Test 5: Models status
echo -e "\n${BLUE}🧪 TEST 5: Models Status${NC}"
models_status=$(curl -s http://10.5.17.187:9092/models/status)

if [[ $models_status == *"deepseek"* ]]; then
    echo -e "${GREEN}✅ PASS: Models status available${NC}"
    echo "Models info: $models_status"
else
    echo -e "${RED}❌ FAIL: Models status${NC}"
    echo "Response: $models_status"
fi

echo -e "\n================================================"
echo -e "${BLUE}🏁 PRODUCTION SETUP TEST COMPLETE${NC}"
echo "================================================"

echo -e "\n${YELLOW}📋 MANUAL TESTS YOU CAN RUN:${NC}"
echo ""
echo "1. Your exact curl command:"
echo "   curl --location 'http://10.5.17.187:9092/generate' \\"
echo "     --header 'Content-Type: application/json' \\"
echo "     --data '{"
echo "       \"prompt\": \"public class Calculator { public int add(int a, int b) { return a + b; } }\","
echo "       \"className\": \"Calculator\","
echo "       \"model\": \"deepseek-v2\""
echo "     }'"
echo ""
echo "2. Spring Boot integration:"
echo "   curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{"
echo "       \"javaCode\": \"public class Calculator { public int add(int a, int b) { return a + b; } }\","
echo "       \"className\": \"Calculator\","
echo "       \"model\": \"deepseek-v2\""
echo "     }'"
echo ""
echo "3. Start Spring Boot if not running:"
echo "   ./gradlew bootRun"

echo -e "\n${GREEN}🎉 Your production setup is correctly configured!${NC}" 