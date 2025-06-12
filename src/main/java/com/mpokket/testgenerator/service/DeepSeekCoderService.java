package com.mpokket.testgenerator.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class DeepSeekCoderService {

    private static final Logger logger = LoggerFactory.getLogger(DeepSeekCoderService.class);
    
    @Value("${deepseek.coder.server.url:http://localhost:8080}")
    private String serverUrl;
    
    @Value("${deepseek.coder.timeout.seconds:180}")
    private int timeoutSeconds;
    
    @Value("${deepseek.coder.max.retries:3}")
    private int maxRetries;
    
    @Value("${deepseek.coder.model.primary:deepseek-v2}")
    private String primaryModel;
    
    @Value("${deepseek.coder.model.auto.selection:true}")
    private boolean autoModelSelection;
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private boolean modelReady = false;
    
    public DeepSeekCoderService() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        
        // Configure timeout for Deepseek-V2 (larger model = longer generation)
        this.restTemplate.getMessageConverters().forEach(converter -> {
            if (converter instanceof org.springframework.http.converter.HttpMessageConverter) {
                // Set timeouts for V2 model (up to 90 seconds)
                Duration timeout = Duration.ofSeconds(timeoutSeconds);
            }
        });
        
        logger.info("Initializing Deepseek-Coder-V2 Service with server URL: {}", serverUrl);
        logger.info("Primary model: {}, Auto-selection: {}", primaryModel, autoModelSelection);
    }
    
    /**
     * Check if Deepseek-Coder models are ready and healthy
     */
    public boolean isModelReady() {
        try {
            String healthUrl = serverUrl + "/health";
            ResponseEntity<String> response = restTemplate.getForEntity(healthUrl, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode healthData = objectMapper.readTree(response.getBody());
                
                // Check both models status
                JsonNode models = healthData.path("models");
                boolean deepseekV2Available = models.path("deepseek-v2").path("status").asText().equals("available");
                boolean deepseek6bAvailable = models.path("deepseek-6b").path("status").asText().equals("loaded");
                
                if (deepseekV2Available || deepseek6bAvailable) {
                    this.modelReady = true;
                    logger.info("Deepseek models status: V2={}, 6B={}", deepseekV2Available, deepseek6bAvailable);
                } else {
                    this.modelReady = false;
                    logger.warn("No Deepseek models available");
                }
                
                return this.modelReady;
            }
        } catch (Exception e) {
            logger.error("Health check failed: {}", e.getMessage());
            this.modelReady = false;
        }
        
        return false;
    }
    
    /**
     * Initialize the Deepseek-Coder models on the server
     */
    public boolean initializeModel() {
        try {
            String initUrl = serverUrl + "/initialize-model";
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model_path", "/home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf");
            requestBody.put("use_gpu", true); // GPU mode for g5.2xlarge
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            logger.info("Attempting to initialize Deepseek-Coder models...");
            ResponseEntity<String> response = restTemplate.postForEntity(initUrl, request, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode responseData = objectMapper.readTree(response.getBody());
                String status = responseData.path("status").asText();
                
                if ("success".equals(status)) {
                    this.modelReady = true;
                    boolean deepseekV2Available = responseData.path("deepseek_v2_available").asBoolean();
                    boolean deepseek6bLoaded = responseData.path("deepseek_loaded").asBoolean();
                    
                    logger.info("Deepseek models initialized: V2={}, 6B={}", deepseekV2Available, deepseek6bLoaded);
                    return true;
                }
            }
            
            logger.error("Failed to initialize Deepseek models");
            return false;
            
        } catch (Exception e) {
            logger.error("Model initialization error: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Get system status from Deepseek-Coder server
     */
    public Map<String, Object> getSystemStatus() {
        try {
            String statusUrl = serverUrl + "/system-status";
            ResponseEntity<String> response = restTemplate.getForEntity(statusUrl, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode statusData = objectMapper.readTree(response.getBody());
                Map<String, Object> status = new HashMap<>();
                
                status.put("server", statusData.path("server").asText("AWS g5.2xlarge"));
                status.put("total_memory_gb", statusData.path("total_memory_gb").asDouble());
                status.put("available_memory_gb", statusData.path("available_memory_gb").asDouble());
                status.put("memory_percent", statusData.path("memory_percent").asDouble());
                status.put("cpu_percent", statusData.path("cpu_percent").asDouble());
                status.put("model_loaded", statusData.path("model_loaded").asBoolean());
                status.put("cache_size", statusData.path("cache_size").asInt());
                
                return status;
            }
        } catch (Exception e) {
            logger.error("Failed to get system status: {}", e.getMessage());
        }
        
        Map<String, Object> errorStatus = new HashMap<>();
        errorStatus.put("error", "Unable to connect to Deepseek-V2 server");
        return errorStatus;
    }
    
    /**
     * Generate JUnit test cases using Deepseek-Coder-V2:16b (Primary) with fallback
     */
    public String generateTestCases(String javaCode, String className) {
        return generateTestCases(javaCode, className, "auto");
    }
    
    /**
     * Generate JUnit test cases with specific model selection
     */
    public String generateTestCases(String javaCode, String className, String modelType) {
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                String response = callDeepSeekCoderServer(javaCode, className, modelType);
                logger.info("Successfully generated test cases for class: {} (length: {} chars)", 
                           className, response.length());
                return response;
                
            } catch (Exception e) {
                logger.error("Deepseek server error (attempt {}): {}", attempt, e.getMessage());
                
                if (attempt == maxRetries) {
                    logger.error("Error generating test cases for class {}: {}", className, e.getMessage());
                    throw new RuntimeException("Failed to generate test cases: " + e.getMessage());
                }
                
                // Wait before retry (longer for V2 model)
                try {
                    Thread.sleep(2000 * attempt);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("Generation interrupted");
                }
            }
        }
        
        throw new RuntimeException("Failed to generate test cases after " + maxRetries + " attempts");
    }
    
    /**
     * Call Deepseek-Coder server with optimized payload for V2 model
     */
    private String callDeepSeekCoderServer(String javaCode, String className, String modelType) throws Exception {
        String generateUrl = serverUrl + "/generate";
        
        // Create optimized request payload for Deepseek-V2
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("prompt", javaCode);
        
        if (className != null && !className.trim().isEmpty()) {
            requestBody.put("className", className.trim());
        }
        
        // NEW: Add model selection for V2 support
        if (modelType != null && !modelType.trim().isEmpty()) {
            requestBody.put("model", modelType.trim()); // "auto", "deepseek-v2", "deepseek-6b"
        } else {
            requestBody.put("model", autoModelSelection ? "auto" : primaryModel);
        }
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("User-Agent", "SpringBoot-DeepSeekV2-Client/2.0");
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
        
        try {
            logger.debug("Sending request to Deepseek-V2 server: {} with model: {}", generateUrl, 
                        requestBody.get("model"));
            ResponseEntity<String> response = restTemplate.postForEntity(generateUrl, request, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode responseData = objectMapper.readTree(response.getBody());
                
                // Extract generated test code
                String generatedTests = responseData.path("response").asText();
                
                if (generatedTests == null || generatedTests.trim().isEmpty()) {
                    throw new RuntimeException("Empty response from Deepseek server");
                }
                
                // Log generation metrics for V2
                double generationTime = responseData.path("generation_time_seconds").asDouble(0.0);
                String modelUsed = responseData.path("model_used").asText("unknown");
                String modelRequested = responseData.path("model_requested").asText("unknown");
                
                // Check available models
                JsonNode availableModels = responseData.path("available_models");
                boolean deepseekV2Available = availableModels.path("deepseek-v2").asBoolean(false);
                boolean deepseek6bAvailable = availableModels.path("deepseek-6b").asBoolean(false);
                
                logger.info("Generation completed in {:.2f}s using {} (requested: {})", 
                           generationTime, modelUsed, modelRequested);
                logger.info("Available models: V2={}, 6B={}", deepseekV2Available, deepseek6bAvailable);
                
                return generatedTests;
            } else {
                throw new RuntimeException("Deepseek server responded with status: " + response.getStatusCode());
            }
            
        } catch (HttpClientErrorException e) {
            String errorBody = e.getResponseBodyAsString();
            logger.error("Client error from Deepseek server: {} - {}", e.getStatusCode(), errorBody);
            throw new RuntimeException("Deepseek server client error: " + e.getStatusCode());
            
        } catch (HttpServerErrorException e) {
            String errorBody = e.getResponseBodyAsString();
            logger.error("Server error from Deepseek: {} - {}", e.getStatusCode(), errorBody);
            
            // Try to parse error details
            try {
                JsonNode errorData = objectMapper.readTree(errorBody);
                String errorMessage = errorData.path("error").asText("Unknown server error");
                throw new RuntimeException("Deepseek server error: " + errorMessage);
            } catch (Exception parseException) {
                throw new RuntimeException("Deepseek server responded with error: " + e.getStatusCode());
            }
            
        } catch (ResourceAccessException e) {
            logger.error("Connection error to Deepseek server: {}", e.getMessage());
            throw new RuntimeException("Cannot connect to Deepseek server at " + serverUrl);
        }
    }
    
    /**
     * Test Deepseek-V2 connectivity
     */
    public Map<String, Object> testDeepSeekV2Connection() {
        try {
            String testUrl = serverUrl + "/test-deepseek-v2";
            ResponseEntity<String> response = restTemplate.postForEntity(testUrl, null, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode responseData = objectMapper.readTree(response.getBody());
                Map<String, Object> result = new HashMap<>();
                
                result.put("status", responseData.path("status").asText());
                result.put("model", responseData.path("model").asText());
                result.put("time", responseData.path("time").asDouble());
                result.put("output", responseData.path("output").asText());
                
                logger.info("Deepseek-V2 test successful: {} in {}s", 
                           result.get("model"), result.get("time"));
                
                return result;
            } else {
                Map<String, Object> error = new HashMap<>();
                error.put("status", "error");
                error.put("message", "HTTP " + response.getStatusCode());
                return error;
            }
        } catch (Exception e) {
            logger.error("Deepseek-V2 test failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "error");
            error.put("message", e.getMessage());
            return error;
        }
    }
    
    /**
     * Get models status
     */
    public Map<String, Object> getModelsStatus() {
        try {
            String statusUrl = serverUrl + "/models/status";
            ResponseEntity<String> response = restTemplate.getForEntity(statusUrl, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode statusData = objectMapper.readTree(response.getBody());
                Map<String, Object> status = new HashMap<>();
                
                // Extract model status information
                JsonNode deepseekV2 = statusData.path("deepseek-v2");
                JsonNode deepseek6b = statusData.path("deepseek-6b");
                
                status.put("deepseek_v2_available", deepseekV2.path("available").asBoolean());
                status.put("deepseek_v2_model", deepseekV2.path("model").asText());
                status.put("deepseek_6b_loaded", deepseek6b.path("loaded").asBoolean());
                status.put("auto_selection_order", statusData.path("auto_selection_order"));
                
                return status;
            }
        } catch (Exception e) {
            logger.error("Failed to get models status: {}", e.getMessage());
        }
        
        Map<String, Object> errorStatus = new HashMap<>();
        errorStatus.put("error", "Unable to get models status");
        return errorStatus;
    }
    
    /**
     * Clear the generation cache on the server
     */
    public boolean clearCache() {
        try {
            String clearCacheUrl = serverUrl + "/clear-cache";
            ResponseEntity<String> response = restTemplate.postForEntity(clearCacheUrl, null, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                logger.info("Deepseek cache cleared successfully");
                return true;
            }
        } catch (Exception e) {
            logger.error("Failed to clear Deepseek cache: {}", e.getMessage());
        }
        
        return false;
    }
    
    /**
     * Generate demo test cases when model is not available
     */
    private String generateDemoTestCases(String className) {
        if (className == null || className.trim().isEmpty()) {
            className = "TestClass";
        }
        
        return String.format("""
                import org.junit.jupiter.api.Test;
                import org.junit.jupiter.api.BeforeEach;
                import org.junit.jupiter.api.DisplayName;
                import static org.junit.jupiter.api.Assertions.*;
                
                @DisplayName("%s Test Suite - Generated by Deepseek-V2 Demo Mode")
                public class %sTest {
                    
                    private %s %s;
                    
                    @BeforeEach
                    void setUp() {
                        %s = new %s();
                    }
                    
                    @Test
                    @DisplayName("Test object initialization")
                    void testObjectInitialization() {
                        assertNotNull(%s);
                    }
                    
                    @Test
                    @DisplayName("Test basic functionality")
                    void testBasicFunctionality() {
                        // TODO: Implement specific tests for %s
                        assertTrue(true, "Placeholder test - implement actual test logic");
                    }
                    
                    @Test
                    @DisplayName("Test edge cases")
                    void testEdgeCases() {
                        // TODO: Add edge case tests for %s
                        assertNotNull(%s);
                    }
                    
                    @Test
                    @DisplayName("Test error conditions")
                    void testErrorConditions() {
                        // TODO: Add error condition tests
                        assertNotNull(%s);
                    }
                }
                """, 
                className, className, className, className.toLowerCase(),
                className.toLowerCase(), className, className.toLowerCase(), 
                className, className, className.toLowerCase(), className.toLowerCase());
    }

    public Map<String, String> generateTestAndSave(String sourceFilePath) throws IOException {
        logger.info("Reading java file from path: {}", sourceFilePath);
        Path sourcePath = Paths.get(sourceFilePath);
        if (!Files.exists(sourcePath)) {
            throw new IOException("File not found at: " + sourceFilePath);
        }

        String javaCode = new String(Files.readAllBytes(sourcePath));
        String className = extractClassName(javaCode);
        
        // This existing method already calls the python service
        String generatedTests = generateTestCases(javaCode, className);

        // Determine the correct test file path
        String testFilePath = sourceFilePath.replace("src/main/java", "src/test/java");
        testFilePath = testFilePath.replace(".java", "Test.java");
        
        Path testPath = Paths.get(testFilePath);
        Files.createDirectories(testPath.getParent());
        Files.write(testPath, generatedTests.getBytes(), StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING);

        logger.info("Successfully wrote generated test to: {}", testFilePath);

        // For now, we can hardcode the model used or retrieve it if the python service returns it
        return Map.of(
            "testFilePath", testFilePath,
            "modelUsed", "Deepseek-Coder Multi-Model" 
        );
    }

    private String extractClassName(String javaCode) {
        // Regex to find public class name, ignoring interfaces and enums
        Pattern pattern = Pattern.compile("public\\s+(?:final\\s+|abstract\\s+)?class\\s+([\\w]+)");
        Matcher matcher = pattern.matcher(javaCode);
        if (matcher.find()) {
            return matcher.group(1);
        }
        // Fallback for non-public classes or different formatting
        pattern = Pattern.compile("class\\s+([\\w]+)");
        matcher = pattern.matcher(javaCode);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return "UnknownClass"; // Default fallback
    }
} 