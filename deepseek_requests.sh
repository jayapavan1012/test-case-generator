#!/bin/bash

# Generated curl commands for DeepSeekTestController.java

# Endpoint: GET /api/deepseek/health
# ✅ SUCCESS Case: No request body needed.
curl -v -X GET 'http://localhost:8081/api/deepseek/health' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/initialize
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/initialize' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/generate-tests
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/generate-tests' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: GET /api/deepseek/system-status
# ✅ SUCCESS Case: No request body needed.
curl -v -X GET 'http://localhost:8081/api/deepseek/system-status' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/clear-cache
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/clear-cache' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: GET /api/deepseek/test
# ✅ SUCCESS Case: No request body needed.
curl -v -X GET 'http://localhost:8081/api/deepseek/test' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/generate
# ✅ SUCCESS Case: Provide a valid request body.
curl -v -X POST 'http://localhost:8081/api/deepseek/generate' -H "Content-Type: application/json" -H "Accept: application/json" --data-raw '"Sample text payload for SUCCESS case."'

# ❌ FAILURE Case: Provide an invalid or incomplete body.
curl -v -X POST 'http://localhost:8081/api/deepseek/generate' -H "Content-Type: application/json" -H "Accept: application/json" --data-raw '"Sample text payload for FAILURE (e.g., missing fields or invalid data) case."'

------------------------------------------------------------

# Endpoint: POST /api/deepseek/generate-tests-v2
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/generate-tests-v2' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/test-deepseek-v2
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/test-deepseek-v2' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: GET /api/deepseek/models-status
# ✅ SUCCESS Case: No request body needed.
curl -v -X GET 'http://localhost:8081/api/deepseek/models-status' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------

# Endpoint: POST /api/deepseek/generate-and-save
# ✅ SUCCESS Case: No request body needed.
curl -v -X POST 'http://localhost:8081/api/deepseek/generate-and-save' -H "Content-Type: application/json" -H "Accept: application/json"

------------------------------------------------------------
