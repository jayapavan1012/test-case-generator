package com.mpokket.testgenerator.controller;

import com.mpokket.testgenerator.service.DeepSeekCoderService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/deepseek")
@CrossOrigin(origins = "*")
public class DeepSeekTestController {

    private static final Logger logger = LoggerFactory.getLogger(DeepSeekTestController.class);

    @Autowired
    private DeepSeekCoderService deepSeekCoderService;

    /**
     * Health check endpoint for Deepseek-Coder system
     */
    @GetMapping(value = "/health", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> health() {
        try {
            Map<String, Object> health = new HashMap<>();
            boolean modelReady = deepSeekCoderService.isModelReady();
            Map<String, Object> systemStatus = deepSeekCoderService.getSystemStatus();
            
            health.put("status", modelReady ? "healthy" : "initializing");
            health.put("model", "Deepseek-Coder-V2:16b + 6.7B Multi-Model");
            health.put("server", "Production Server (10.5.17.187:9092)");
            health.put("model_ready", modelReady);
            health.put("system_status", systemStatus);
            health.put("specialization", "Java JUnit 5 test generation");
            health.put("optimizations", Map.of(
                "primary_model", "Deepseek-Coder-V2:16b (Ollama)",
                "fallback_model", "Deepseek-Coder 6.7B (Q4_K_M)",
                "context_window", "16K tokens (V2), 8K tokens (6B)",
                "auto_selection", "V2 → 6B → Demo fallback",
                "generation_speed", "15-45s (V2), 3-15s (6B)"
            ));
            
            return ResponseEntity.ok(health);
            
        } catch (Exception e) {
            logger.error("Health check error: {}", e.getMessage());
            Map<String, Object> errorHealth = new HashMap<>();
            errorHealth.put("status", "error");
            errorHealth.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(errorHealth);
        }
    }

    /**
     * Initialize Deepseek-Coder model
     */
    @PostMapping(value = "/initialize", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> initializeModel() {
        try {
            logger.info("Initializing Deepseek-Coder multi-model system...");
            boolean success = deepSeekCoderService.initializeModel();
            
            Map<String, Object> response = new HashMap<>();
            if (success) {
                response.put("status", "success");
                response.put("message", "Deepseek-Coder multi-model system initialized successfully");
                response.put("primary_model", "Deepseek-Coder-V2:16b (Ollama)");
                response.put("fallback_model", "Deepseek-Coder 6.7B-Instruct (Q4_K_M)");
                response.put("server", "Production Server (10.5.17.187:9092)");
                return ResponseEntity.ok(response);
            } else {
                response.put("status", "error");
                response.put("message", "Failed to initialize Deepseek-Coder models");
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
            }
            
        } catch (Exception e) {
            logger.error("Model initialization error: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", "Initialization failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Generate JUnit tests for Java code using Deepseek-Coder
     */
    @PostMapping(value = "/generate-tests", 
                 consumes = MediaType.APPLICATION_JSON_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> generateTests(@RequestBody Map<String, Object> request) {
        try {
            String javaCode = (String) request.get("javaCode");
            String className = (String) request.get("className");
            
            if (javaCode == null || javaCode.trim().isEmpty()) {
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("error", "Java code is required");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            logger.info("Generating tests for class: {} using Deepseek-Coder", 
                       className != null ? className : "unknown");
            
            long startTime = System.currentTimeMillis();
            String generatedTests = deepSeekCoderService.generateTestCases(javaCode, className);
            long generationTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> response = new HashMap<>();
            response.put("generatedTests", generatedTests);
            response.put("className", className);
            response.put("generationTimeMs", generationTime);
            response.put("model", "Deepseek-Coder Multi-Model (Auto-Selection)");
            response.put("server", "Production Server (10.5.17.187:9092)");
            response.put("testFramework", "JUnit 5");
            
            logger.info("Test generation completed in {}ms for class: {}", generationTime, className);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error generating class tests: ", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", "Failed to generate tests: " + e.getMessage());
            errorResponse.put("server", "Production Server (10.5.17.187:9092)");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Get system status and resource usage
     */
    @GetMapping(value = "/system-status", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> getSystemStatus() {
        try {
            Map<String, Object> status = deepSeekCoderService.getSystemStatus();
            status.put("endpoint", "/api/deepseek/system-status");
            status.put("timestamp", System.currentTimeMillis());
            
            return ResponseEntity.ok(status);
            
        } catch (Exception e) {
            logger.error("Error getting system status: {}", e.getMessage());
            Map<String, Object> errorStatus = new HashMap<>();
            errorStatus.put("error", "Failed to get system status: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorStatus);
        }
    }

    /**
     * Clear generation cache
     */
    @PostMapping(value = "/clear-cache", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> clearCache() {
        try {
            boolean success = deepSeekCoderService.clearCache();
            
            Map<String, Object> response = new HashMap<>();
            if (success) {
                response.put("status", "success");
                response.put("message", "Deepseek-Coder cache cleared successfully");
            } else {
                response.put("status", "error");
                response.put("message", "Failed to clear cache");
            }
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error clearing cache: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", "Cache clear failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Test endpoint for quick verification
     */
    @GetMapping(value = "/test", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> testEndpoint() {
        Map<String, Object> response = new HashMap<>();
        response.put("message", "Deepseek-Coder-V2 Test Generator API is running");
        response.put("primary_model", "Deepseek-Coder-V2:16b (Ollama)");
        response.put("fallback_model", "Deepseek-Coder 6.7B-Instruct (Q4_K_M)");
        response.put("server", "Production Server (10.5.17.187:9092)");
        response.put("endpoints", Map.of(
            "health", "/api/deepseek/health",
            "initialize", "/api/deepseek/initialize",
            "generate", "/api/deepseek/generate-tests",
            "generate-v2", "/api/deepseek/generate-tests-v2",
            "models-status", "/api/deepseek/models-status",
            "system-status", "/api/deepseek/system-status",
            "test-v2", "/api/deepseek/test-deepseek-v2",
            "cache", "/api/deepseek/clear-cache"
        ));
        response.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(response);
    }

    /**
     * Generate tests with simple string input (backward compatibility)
     */
    @PostMapping(value = "/generate", 
                 consumes = MediaType.TEXT_PLAIN_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> generateTestsSimple(@RequestBody String javaCode) {
        try {
            if (javaCode == null || javaCode.trim().isEmpty()) {
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("error", "Java code is required");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // Extract class name from code
            String className = extractClassName(javaCode);
            
            logger.info("Generating tests for class: {} (simple endpoint)", className);
            
            long startTime = System.currentTimeMillis();
            String generatedTests = deepSeekCoderService.generateTestCases(javaCode, className);
            long generationTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> response = new HashMap<>();
            response.put("generatedTests", generatedTests);
            response.put("className", className);
            response.put("generationTimeMs", generationTime);
            response.put("model", "Deepseek-Coder Multi-Model (Simple)");
            response.put("server", "Production Server (10.5.17.187:9092)");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error in simple generate endpoint: ", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", "Failed to generate tests: " + e.getMessage());
            errorResponse.put("server", "Production Server (10.5.17.187:9092)");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Extract class name from Java code
     */
    private String extractClassName(String javaCode) {
        try {
            for (String line : javaCode.split("\n")) {
                if (line.contains("class ") && (line.contains("public ") || line.contains("private ") || line.contains("protected "))) {
                    String[] parts = line.split("class ");
                    if (parts.length > 1) {
                        return parts[1].split(" ")[0].split("\\{")[0].split("<")[0].trim();
                    }
                }
            }
        } catch (Exception e) {
            logger.warn("Failed to extract class name: {}", e.getMessage());
        }
        return "UnknownClass";
    }

    /**
     * Generate JUnit tests for Java code using Deepseek-V2 with model selection
     */
    @PostMapping(value = "/generate-tests-v2", 
                 consumes = MediaType.APPLICATION_JSON_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> generateTestsV2(@RequestBody Map<String, Object> request) {
        try {
            String javaCode = (String) request.get("javaCode");
            String className = (String) request.get("className");
            String modelType = (String) request.getOrDefault("model", "auto"); // NEW: model selection
            
            if (javaCode == null || javaCode.trim().isEmpty()) {
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("error", "Java code is required");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // Validate model type
            if (!modelType.matches("auto|deepseek-v2|deepseek-6b|demo")) {
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("error", "Invalid model type. Valid options: auto, deepseek-v2, deepseek-6b, demo");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            logger.info("Generating tests for class: {} using model: {}", 
                       className != null ? className : "unknown", modelType);
            
            long startTime = System.currentTimeMillis();
            String generatedTests = deepSeekCoderService.generateTestCases(javaCode, className, modelType);
            long generationTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> response = new HashMap<>();
            response.put("generatedTests", generatedTests);
            response.put("className", className);
            response.put("generationTimeMs", generationTime);
            response.put("modelRequested", modelType);
            response.put("server", "Production Server (10.5.17.187:9092)");
            response.put("testFramework", "JUnit 5");
            response.put("version", "Deepseek-V2 Multi-Model");
            
            logger.info("Test generation completed in {}ms for class: {} using model: {}", 
                       generationTime, className, modelType);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error generating V2 tests: ", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", "Failed to generate tests: " + e.getMessage());
            errorResponse.put("server", "Production Server (10.5.17.187:9092)");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Test Deepseek-V2 connectivity
     */
    @PostMapping(value = "/test-deepseek-v2", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> testDeepSeekV2() {
        try {
            Map<String, Object> result = deepSeekCoderService.testDeepSeekV2Connection();
            
            if ("success".equals(result.get("status"))) {
                return ResponseEntity.ok(result);
            } else {
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(result);
            }
            
        } catch (Exception e) {
            logger.error("Deepseek-V2 test error: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", "V2 test failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Get models status
     */
    @GetMapping(value = "/models-status", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> getModelsStatus() {
        try {
            Map<String, Object> status = deepSeekCoderService.getModelsStatus();
            status.put("endpoint", "/api/deepseek/models-status");
            status.put("timestamp", System.currentTimeMillis());
            
            return ResponseEntity.ok(status);
            
        } catch (Exception e) {
            logger.error("Error getting models status: {}", e.getMessage());
            Map<String, Object> errorStatus = new HashMap<>();
            errorStatus.put("error", "Failed to get models status: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorStatus);
        }
    }

    /**
     * Generate a test file from a given Java class file path and save it.
     */
    @PostMapping(value = "/generate-and-save", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> generateAndSaveTest(@RequestBody Map<String, String> request) {
        String filePath = request.get("filePath");
        if (filePath == null || filePath.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "filePath is required"));
        }

        try {
            logger.info("Received request to generate and save test for file: {}", filePath);
            Map<String, String> result = deepSeekCoderService.generateTestAndSave(filePath);
            logger.info("Successfully generated and saved test file at: {}", result.get("testFilePath"));
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "Test file generated and saved successfully.",
                "sourceFilePath", filePath,
                "testFilePath", result.get("testFilePath"),
                "modelUsed", result.get("modelUsed")
            ));
        } catch (Exception e) {
            logger.error("Failed to generate and save test for path '{}': {}", filePath, e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                                 .body(Map.of("error", "Failed to process file: " + e.getMessage()));
        }
    }
} 