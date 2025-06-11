package com.mpokket.testgenerator.controller;

import com.mpokket.testgenerator.service.LLMService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for test generation endpoints
 */
@RestController
@RequestMapping("/api/test-generation")
@Slf4j
public class TestGenerationController {

    @Autowired
    private LLMService llmService;

    /**
     * Health check endpoint for LLM service
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "test-generation");
        response.put("modelReady", llmService.isModelReady());
        response.put("status", llmService.isModelReady() ? "healthy" : "model not ready");
        return ResponseEntity.ok(response);
    }

    /**
     * Generate JUnit test cases for a Java class
     */
    @PostMapping("/generate-class-tests")
    public ResponseEntity<Map<String, Object>> generateClassTests(
            @RequestBody Map<String, String> request) {
        
        try {
            String javaCode = request.get("javaCode");
            String className = request.get("className");
            String existingTestStyle = request.get("existingTestStyle");

            if (javaCode == null || className == null) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "javaCode and className are required"));
            }

            log.info("Generating tests for class: {}", className);
            String generatedTests = llmService.generateTestCases(javaCode, className, existingTestStyle);

            Map<String, Object> response = new HashMap<>();
            response.put("className", className);
            response.put("generatedTests", generatedTests);
            response.put("success", true);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Error generating class tests: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", e.getMessage(), "success", false));
        }
    }

    /**
     * Generate test methods for a specific method
     */
    @PostMapping("/generate-method-tests")
    public ResponseEntity<Map<String, Object>> generateMethodTests(
            @RequestBody Map<String, String> request) {
        
        try {
            String methodSignature = request.get("methodSignature");
            String methodBody = request.get("methodBody");
            String className = request.get("className");

            if (methodSignature == null || methodBody == null || className == null) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "methodSignature, methodBody, and className are required"));
            }

            log.info("Generating tests for method: {} in class: {}", methodSignature, className);
            List<String> testMethods = llmService.generateMethodTests(methodSignature, methodBody, className);

            Map<String, Object> response = new HashMap<>();
            response.put("methodSignature", methodSignature);
            response.put("className", className);
            response.put("testMethods", testMethods);
            response.put("testCount", testMethods.size());
            response.put("success", true);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Error generating method tests: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", e.getMessage(), "success", false));
        }
    }

    /**
     * Analyze existing test patterns
     */
    @PostMapping("/analyze-test-patterns")
    public ResponseEntity<Map<String, Object>> analyzeTestPatterns(
            @RequestBody Map<String, List<String>> request) {
        
        try {
            List<String> existingTests = request.get("existingTests");

            if (existingTests == null || existingTests.isEmpty()) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "existingTests list is required and cannot be empty"));
            }

            log.info("Analyzing test patterns for {} test files", existingTests.size());
            Map<String, Object> patterns = llmService.analyzeTestPatterns(existingTests);

            Map<String, Object> response = new HashMap<>();
            response.put("patterns", patterns);
            response.put("testFilesAnalyzed", existingTests.size());
            response.put("success", true);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Error analyzing test patterns: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", e.getMessage(), "success", false));
        }
    }

    /**
     * Initialize the LLM model
     */
    @PostMapping("/initialize-model")
    public ResponseEntity<Map<String, Object>> initializeModel() {
        try {
            log.info("Initializing LLM model...");
            boolean success = llmService.initializeModel();
            
            Map<String, Object> response = new HashMap<>();
            response.put("initialized", success);
            response.put("message", success ? "Model initialized successfully" : "Failed to initialize model");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error initializing model: ", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", e.getMessage(), "initialized", false));
        }
    }

    /**
     * Get model status and configuration
     */
    @GetMapping("/model-status")
    public ResponseEntity<Map<String, Object>> getModelStatus() {
        Map<String, Object> response = new HashMap<>();
        response.put("modelReady", llmService.isModelReady());
        response.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(response);
    }
} 