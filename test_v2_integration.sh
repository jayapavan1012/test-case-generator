#!/bin/bash

echo "🚀 DEEPSEEK-CODER-V2:16B INTEGRATION TEST SUITE"
echo "=================================================================="
echo "Testing Spring Boot ↔ Python Server ↔ Ollama Integration"
echo "=================================================================="

# Configuration
PYTHON_SERVER_URL="http://10.5.17.187:9092"
SPRING_BOOT_URL="http://localhost:8081"
LOG_FILE="integration_test.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -e "\n${BLUE}🧪 TEST: $test_name${NC}"
    log "Running test: $test_name"
    
    # Execute test command
    local result
    result=$(eval "$test_command" 2>&1)
    local exit_code=$?
    
    # Check result
    if [[ $exit_code -eq 0 ]] && [[ $result =~ $expected_pattern ]]; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        log "PASS: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        echo -e "${RED}Result: $result${NC}"
        log "FAIL: $test_name - $result"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Clear previous log
> $LOG_FILE

echo -e "\n${YELLOW}📋 PHASE 1: PYTHON SERVER TESTS (10.5.17.187:9092)${NC}"
echo "=================================================="

# Test 1: Python server health
run_test "Python Server Health Check" \
    "curl -s $PYTHON_SERVER_URL/health" \
    "healthy"

# Test 2: Models status
run_test "Models Status Check" \
    "curl -s $PYTHON_SERVER_URL/models/status" \
    "deepseek"

# Test 3: Deepseek-V2 connectivity (if available)
run_test "Deepseek-V2 Connectivity Test" \
    "curl -s -X POST $PYTHON_SERVER_URL/test-deepseek-v2" \
    "status"

# Test 4: Python server generation (auto model)
TEST_JAVA_CODE='public class Calculator { public int add(int a, int b) { return a + b; } }'
run_test "Python Server Generation (Auto)" \
    "curl -s -X POST $PYTHON_SERVER_URL/generate -H 'Content-Type: application/json' -d '{\"prompt\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\"}'" \
    "response"

# Test 5: Python server generation (specific model)
run_test "Python Server Generation (Deepseek-V2)" \
    "curl -s -X POST $PYTHON_SERVER_URL/generate -H 'Content-Type: application/json' -d '{\"prompt\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\",\"model\":\"deepseek-v2\"}'" \
    "response"

echo -e "\n${YELLOW}📋 PHASE 2: SPRING BOOT SERVER TESTS (localhost:8081)${NC}"
echo "=================================================="

# Test 6: Spring Boot health
run_test "Spring Boot Health Check" \
    "curl -s $SPRING_BOOT_URL/api/deepseek/health" \
    "healthy"

# Test 7: Spring Boot models status
run_test "Spring Boot Models Status" \
    "curl -s $SPRING_BOOT_URL/api/deepseek/models-status" \
    "deepseek"

# Test 8: Spring Boot V2 test
run_test "Spring Boot Deepseek-V2 Test" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/test-deepseek-v2" \
    "status"

echo -e "\n${YELLOW}📋 PHASE 3: END-TO-END INTEGRATION TESTS${NC}"
echo "=================================================="

# Test 9: Spring Boot generation (legacy endpoint)
run_test "Spring Boot Generation (Legacy)" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests -H 'Content-Type: application/json' -d '{\"javaCode\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\"}'" \
    "generatedTests"

# Test 10: Spring Boot generation (V2 endpoint - auto)
run_test "Spring Boot V2 Generation (Auto)" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\",\"model\":\"auto\"}'" \
    "generatedTests"

# Test 11: Spring Boot generation (V2 endpoint - specific model)
run_test "Spring Boot V2 Generation (Deepseek-V2)" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\",\"model\":\"deepseek-v2\"}'" \
    "generatedTests"

# Test 12: Complex Java class test
COMPLEX_JAVA='public class BankAccount { private double balance; public BankAccount(double initialBalance) { this.balance = initialBalance; } public void deposit(double amount) { if (amount > 0) balance += amount; } public boolean withdraw(double amount) { if (amount > 0 && amount <= balance) { balance -= amount; return true; } return false; } public double getBalance() { return balance; } }'

run_test "Complex Class Generation Test" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"$COMPLEX_JAVA\",\"className\":\"BankAccount\",\"model\":\"auto\"}'" \
    "generatedTests.*BankAccount"

echo -e "\n${YELLOW}📋 PHASE 4: PERFORMANCE TESTS${NC}"
echo "=================================================="

# Test 13: Cache test
run_test "Cache Clear Test" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/clear-cache" \
    "success"

# Test 14: System status
run_test "System Status Test" \
    "curl -s $SPRING_BOOT_URL/api/deepseek/system-status" \
    "memory"

echo -e "\n${YELLOW}📋 PHASE 5: ERROR HANDLING TESTS${NC}"
echo "=================================================="

# Test 15: Invalid model type
run_test "Invalid Model Type Handling" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"$TEST_JAVA_CODE\",\"className\":\"Calculator\",\"model\":\"invalid-model\"}'" \
    "error.*Invalid model type"

# Test 16: Empty Java code
run_test "Empty Java Code Handling" \
    "curl -s -X POST $SPRING_BOOT_URL/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"\",\"className\":\"Calculator\",\"model\":\"auto\"}'" \
    "error.*required"

echo -e "\n=================================================================="
echo -e "${BLUE}🏁 INTEGRATION TEST SUMMARY${NC}"
echo "=================================================================="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Integration is working correctly.${NC}"
    echo -e "${GREEN}✨ Deepseek-Coder-V2:16b integration is ready for production!${NC}"
    exit 0
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "\n${YELLOW}⚠️  Most tests passed ($SUCCESS_RATE%). Check failed tests.${NC}"
    exit 1
else
    echo -e "\n${RED}💥 Multiple integration issues detected ($SUCCESS_RATE% success rate).${NC}"
    echo -e "${RED}❌ Integration requires fixes before production use.${NC}"
    exit 2
fi 