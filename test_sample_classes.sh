#!/bin/bash

echo "🧪 SPRING BOOT API - SAMPLE CLASS TESTS"
echo "================================================"
echo "Testing various Java classes with Spring Boot API"
echo "Endpoint: http://localhost:8081/api/deepseek/generate-tests-v2"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to test class generation
test_class() {
    local class_name="$1"
    local java_code="$2"
    local model="${3:-auto}"
    
    echo -e "\n${BLUE}🧪 Testing: $class_name${NC}"
    echo "Model: $model"
    
    response=$(curl -s -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
      -H "Content-Type: application/json" \
      -d "{
        \"javaCode\": \"$java_code\",
        \"className\": \"$class_name\",
        \"model\": \"$model\"
      }")
    
    if [[ $response == *"generatedTests"* ]]; then
        echo -e "${GREEN}✅ SUCCESS: Generated tests for $class_name${NC}"
        
        # Extract and show test length
        test_length=$(echo "$response" | jq -r '.generatedTests' 2>/dev/null | wc -c)
        generation_time=$(echo "$response" | jq -r '.generationTimeMs' 2>/dev/null)
        model_used=$(echo "$response" | jq -r '.modelUsed // "unknown"' 2>/dev/null)
        
        echo "   Test length: $test_length characters"
        echo "   Generation time: ${generation_time}ms"
        echo "   Model used: $model_used"
    else
        echo -e "${RED}❌ FAILED: $class_name${NC}"
        echo "Response: $response"
    fi
}

# Check if Spring Boot is running
echo -e "${YELLOW}📋 Checking Spring Boot status...${NC}"
health_check=$(curl -s http://localhost:8081/api/deepseek/health 2>/dev/null)

if [[ $health_check != *"healthy"* ]]; then
    echo -e "${RED}❌ Spring Boot is not running or not healthy${NC}"
    echo "Please start Spring Boot with: ./gradlew bootRun"
    exit 1
fi

echo -e "${GREEN}✅ Spring Boot is running${NC}"

# Test 1: Simple Calculator
test_class "Calculator" \
"public class Calculator { public int add(int a, int b) { return a + b; } public int subtract(int a, int b) { return a - b; } public int multiply(int a, int b) { return a * b; } public double divide(int a, int b) { if (b == 0) throw new IllegalArgumentException(\"Cannot divide by zero\"); return (double) a / b; } }" \
"auto"

# Test 2: BankAccount with constructor
test_class "BankAccount" \
"public class BankAccount { private double balance; public BankAccount(double initialBalance) { if (initialBalance < 0) throw new IllegalArgumentException(\"Initial balance cannot be negative\"); this.balance = initialBalance; } public void deposit(double amount) { if (amount > 0) balance += amount; } public boolean withdraw(double amount) { if (amount > 0 && amount <= balance) { balance -= amount; return true; } return false; } public double getBalance() { return balance; } }" \
"deepseek-v2"

# Test 3: StringUtils static methods
test_class "StringUtils" \
"public class StringUtils { public static boolean isEmpty(String str) { return str == null || str.length() == 0; } public static boolean isNotEmpty(String str) { return !isEmpty(str); } public static String reverse(String str) { if (isEmpty(str)) return str; return new StringBuilder(str).reverse().toString(); } public static int countVowels(String str) { if (isEmpty(str)) return 0; int count = 0; String vowels = \"aeiouAEIOU\"; for (char c : str.toCharArray()) { if (vowels.indexOf(c) != -1) count++; } return count; } }" \
"deepseek-6b"

# Test 4: Simple Person class
test_class "Person" \
"public class Person { private String name; private int age; public Person(String name, int age) { this.name = name; this.age = age; } public String getName() { return name; } public void setName(String name) { this.name = name; } public int getAge() { return age; } public void setAge(int age) { this.age = age; } public boolean isAdult() { return age >= 18; } }" \
"auto"

# Test 5: ShoppingCart
test_class "ShoppingCart" \
"public class ShoppingCart { private List<String> items = new ArrayList<>(); private double total = 0.0; public void addItem(String item, double price) { if (item != null && price > 0) { items.add(item); total += price; } } public void removeItem(String item, double price) { if (items.remove(item)) { total -= price; } } public int getItemCount() { return items.size(); } public double getTotal() { return total; } public void clear() { items.clear(); total = 0.0; } }" \
"auto"

echo -e "\n================================================"
echo -e "${BLUE}🏁 SAMPLE CLASS TESTS COMPLETE${NC}"
echo "================================================"

echo -e "\n${YELLOW}📋 MANUAL CURL COMMANDS:${NC}"
echo ""
echo "Calculator:"
echo "curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"public class Calculator { public int add(int a, int b) { return a + b; } }\",\"className\":\"Calculator\",\"model\":\"auto\"}'"
echo ""
echo "BankAccount:"
echo "curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"public class BankAccount { private double balance; public void deposit(double amount) { balance += amount; } }\",\"className\":\"BankAccount\",\"model\":\"deepseek-v2\"}'"
echo ""
echo "StringUtils:"
echo "curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 -H 'Content-Type: application/json' -d '{\"javaCode\":\"public class StringUtils { public static boolean isEmpty(String str) { return str == null || str.length() == 0; } }\",\"className\":\"StringUtils\",\"model\":\"deepseek-6b\"}'" 