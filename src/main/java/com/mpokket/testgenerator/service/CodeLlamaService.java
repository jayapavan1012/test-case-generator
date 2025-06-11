package com.mpokket.testgenerator.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * Service specifically for CodeLlama 13B Instruct model running on EC2
 * Optimized for JUnit test generation
 */
@Service
@Slf4j
public class CodeLlamaService implements LLMService {

    @Value("${llm.server-url:http://10.5.17.187:8082}")
    private String serverUrl;

    @Value("${llm.timeout-seconds:120}")
    private int timeoutSeconds;

    @Value("${llm.max-retries:3}")
    private int maxRetries;

    @Value("${llm.max-tokens:2048}")
    private int maxTokens;

    @Value("${llm.temperature:0.1}")
    private double temperature;

    private OkHttpClient httpClient;
    private ObjectMapper objectMapper;
    private volatile boolean modelReady = false;

    @PostConstruct
    public void init() {
        log.info("Initializing CodeLlama Service with server URL: {}", serverUrl);
        
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .readTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .writeTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .build();
        
        this.objectMapper = new ObjectMapper();
        
        // Check if CodeLlama model is ready
        checkModelStatus();
    }

    @PreDestroy
    public void cleanup() {
        if (httpClient != null) {
            httpClient.dispatcher().executorService().shutdown();
            httpClient.connectionPool().evictAll();
        }
    }

    @Override
    public String generateTestCases(String javaCode, String className, String existingTestStyle) {
        if (!modelReady) {
            log.warn("CodeLlama model not ready, attempting to initialize...");
            if (!initializeModel()) {
                throw new RuntimeException("CodeLlama model is not ready and failed to initialize");
            }
        }

        try {
            String response = callCodeLlamaServer(javaCode);
            log.info("Successfully generated test cases for class: {} (length: {} chars)", className, response.length());
            return response;
        } catch (Exception e) {
            log.error("Error generating test cases for class {}: {}", className, e.getMessage());
            throw new RuntimeException("Failed to generate test cases: " + e.getMessage(), e);
        }
    }

    @Override
    public List<String> generateMethodTests(String methodSignature, String methodBody, String className) {
        if (!modelReady) {
            log.warn("CodeLlama model not ready, attempting to initialize...");
            if (!initializeModel()) {
                throw new RuntimeException("CodeLlama model is not ready and failed to initialize");
            }
        }

        String methodCode = methodSignature + " {\n" + methodBody + "\n}";
        
        try {
            String response = callCodeLlamaServer(methodCode);
            // Parse the response and extract individual test methods
            List<String> testMethods = parseTestMethods(response);
            log.info("Successfully generated {} test methods for method in class: {}", testMethods.size(), className);
            return testMethods;
        } catch (Exception e) {
            log.error("Error generating method tests for class {}: {}", className, e.getMessage());
            throw new RuntimeException("Failed to generate method tests: " + e.getMessage(), e);
        }
    }

    @Override
    public Map<String, Object> analyzeTestPatterns(List<String> existingTests) {
        // For now, return a simple pattern analysis
        Map<String, Object> patterns = new HashMap<>();
        patterns.put("test_framework", "JUnit 5");
        patterns.put("assertion_style", "Standard JUnit assertions");
        patterns.put("naming_convention", "testMethodName_WhenCondition_ThenExpectedResult");
        patterns.put("analyzed_files", existingTests.size());
        
        log.info("Analyzed {} test files for patterns", existingTests.size());
        return patterns;
    }

    @Override
    public boolean isModelReady() {
        return modelReady;
    }

    @Override
    public boolean initializeModel() {
        try {
            log.info("Attempting to initialize CodeLlama model...");
            
            // First check health
            Response healthResponse = httpClient.newCall(
                new Request.Builder()
                    .url(serverUrl + "/health")
                    .get()
                    .build()
            ).execute();
            
            if (!healthResponse.isSuccessful()) {
                log.error("CodeLlama server health check failed: {}", healthResponse.code());
                return false;
            }

            // Parse health response to check if model is loaded
            String healthBody = healthResponse.body().string();
            JsonNode healthJson = objectMapper.readTree(healthBody);
            boolean modelLoaded = healthJson.get("model_loaded").asBoolean();
            
            if (!modelLoaded) {
                log.info("Model not loaded, attempting to initialize...");
                
                // Initialize model
                Map<String, Object> initRequest = new HashMap<>();
                initRequest.put("model_path", "/home/adminuser/models/codellama-13b-instruct.Q4_K_M.gguf");
                
                RequestBody initBody = RequestBody.create(
                    objectMapper.writeValueAsString(initRequest),
                    MediaType.get("application/json")
                );

                Response initResponse = httpClient.newCall(
                    new Request.Builder()
                        .url(serverUrl + "/initialize-model")
                        .post(initBody)
                        .build()
                ).execute();
                
                if (!initResponse.isSuccessful()) {
                    log.error("Failed to initialize CodeLlama model: {}", initResponse.code());
                    return false;
                }
            }
            
            modelReady = true;
            log.info("CodeLlama model initialized successfully");
            return true;
            
        } catch (Exception e) {
            log.error("Failed to initialize CodeLlama model: {}", e.getMessage());
            modelReady = false;
            return false;
        }
    }

    private void checkModelStatus() {
        try {
            Response response = httpClient.newCall(
                new Request.Builder()
                    .url(serverUrl + "/health")
                    .get()
                    .build()
            ).execute();
            
            if (response.isSuccessful()) {
                String responseBody = response.body().string();
                JsonNode jsonResponse = objectMapper.readTree(responseBody);
                modelReady = jsonResponse.get("model_loaded").asBoolean();
                log.info("CodeLlama model status check: {}", modelReady ? "Ready" : "Not ready");
            } else {
                modelReady = false;
                log.warn("CodeLlama server not responding: {}", response.code());
            }
        } catch (Exception e) {
            log.warn("Could not check CodeLlama model status: {}", e.getMessage());
            modelReady = false;
        }
    }

    private String callCodeLlamaServer(String javaCode) throws IOException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("prompt", javaCode);

        RequestBody body = RequestBody.create(
            objectMapper.writeValueAsString(requestBody),
            MediaType.get("application/json")
        );

        Request request = new Request.Builder()
            .url(serverUrl + "/generate")
            .post(body)
            .build();

        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                log.debug("Calling CodeLlama server, attempt {} of {}", attempt, maxRetries);
                
                Response response = httpClient.newCall(request).execute();
                
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    JsonNode jsonResponse = objectMapper.readTree(responseBody);
                    
                    if (jsonResponse.has("response")) {
                        return jsonResponse.get("response").asText();
                    } else {
                        log.error("Unexpected response format from CodeLlama server: {}", responseBody);
                        throw new IOException("Invalid response format");
                    }
                } else {
                    String errorBody = response.body() != null ? response.body().string() : "No error details";
                    log.error("CodeLlama server error (attempt {}): {} - {}", attempt, response.code(), errorBody);
                    
                    if (attempt == maxRetries) {
                        throw new IOException("CodeLlama server responded with error: " + response.code());
                    }
                }
                
                // Wait before retry
                if (attempt < maxRetries) {
                    try {
                        Thread.sleep(1000 * attempt); // Exponential backoff
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        throw new IOException("Request interrupted");
                    }
                }
                
            } catch (IOException e) {
                if (attempt == maxRetries) {
                    throw e;
                }
                log.warn("Network error on attempt {} of {}: {}", attempt, maxRetries, e.getMessage());
            }
        }
        
        throw new IOException("Failed to get response from CodeLlama server after " + maxRetries + " attempts");
    }

    private List<String> parseTestMethods(String response) {
        List<String> methods = new ArrayList<>();
        String[] lines = response.split("\n");
        StringBuilder currentMethod = new StringBuilder();
        int braceCount = 0;
        boolean inMethod = false;

        for (String line : lines) {
            String trimmedLine = line.trim();
            
            // Check if this is a test method start
            if (trimmedLine.contains("@Test") || 
                (trimmedLine.contains("void test") && trimmedLine.contains("()"))) {
                if (inMethod && currentMethod.length() > 0) {
                    methods.add(currentMethod.toString().trim());
                }
                currentMethod = new StringBuilder();
                inMethod = true;
                braceCount = 0;
            }
            
            if (inMethod) {
                currentMethod.append(line).append("\n");
                braceCount += countBraces(line, '{') - countBraces(line, '}');
                
                if (braceCount <= 0 && line.trim().endsWith("}")) {
                    methods.add(currentMethod.toString().trim());
                    currentMethod = new StringBuilder();
                    inMethod = false;
                }
            }
        }
        
        if (inMethod && currentMethod.length() > 0) {
            methods.add(currentMethod.toString().trim());
        }
        
        return methods;
    }

    private int countBraces(String line, char brace) {
        return (int) line.chars().filter(ch -> ch == brace).count();
    }
} 