#!/bin/bash
# This script generates curl commands to test the endpoints of the DeepSeekTestController in a Spring Boot application.
# It is recommended to have 'jq' installed for better JSON formatting, although it is not strictly necessary.

echo "=============================================="
echo "--- Testing: Health Check - SUCCESS ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8081/api/deepseek/health)
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Initialize Model - SUCCESS ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8081/api/deepseek/initialize)
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Generate Tests - SUCCESS ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8081/api/deepseek/generate-tests \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
--data-raw '{
    "javaCode": "public class SampleTest { public void sampleMethod() {} }",
    "className": "SampleTest"
}')
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Generate Tests - FAILURE ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8081/api/deepseek/generate-tests \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
--data-raw '{
    "javaCode": "",
    "className": ""
}')
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Get System Status - SUCCESS ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8081/api/deepseek/system-status)
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Clear Cache - SUCCESS ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8081/api/deepseek/clear-cache)
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""

echo "=============================================="
echo "--- Testing: Clear Cache - FAILURE ---"
echo "=============================================="

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8081/api/deepseek/clear-cache)
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')

echo "--> STATUS: $HTTP_STATUS"
echo "--> RESPONSE BODY:"
if command -v jq >/dev/null; then
    echo "$HTTP_BODY" | jq .
else
    echo "NOTE: 'jq' is not installed. Displaying raw JSON."
    echo "$HTTP_BODY"
fi
echo ""