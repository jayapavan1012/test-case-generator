package com.mpokket.testgenerator.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import lombok.Data;

/**
 * Configuration class for LLM (Large Language Model) settings
 */
@Configuration
@ConfigurationProperties(prefix = "llm")
@Data
public class LLMConfig {
    
    // Model Configuration
    private String modelName = "meta-llama/Llama-2-7b-chat-hf";
    private String modelPath = "./models/llama-2-7b-chat";
    private String pythonScriptPath = "./python/llm_server.py";
    private String serverUrl = "http://localhost:8080";
    private int serverPort = 8080;
    
    // Model Parameters
    private int maxTokens = 2048;
    private double temperature = 0.7;
    private double topP = 0.9;
    private int topK = 50;
    private String stopSequences = "</s>,\n\n";
    
    // Performance Settings
    private int maxRetries = 3;
    private long timeoutSeconds = 30;
    private boolean enableCaching = true;
    private int cacheSize = 100;
    private long cacheExpirationMinutes = 60;
    
    // Context Management
    private int maxContextLength = 4096;
    private int contextOverlapTokens = 200;
    
    // Prompt Templates
    private String testGenerationPrompt = """
        You are an expert Java developer and test engineer. Generate comprehensive JUnit 5 test cases for the following Java code.
        
        Requirements:
        1. Create thorough test coverage including edge cases
        2. Use proper JUnit 5 annotations and assertions
        3. Follow best practices for unit testing
        4. Include setup and teardown methods if needed
        5. Test both positive and negative scenarios
        
        Java Code:
        ```java
        %s
        ```
        
        Class Name: %s
        
        %s
        
        Generate complete test class:
        """;
        
    private String methodTestPrompt = """
        Generate JUnit 5 test methods for this specific Java method:
        
        Method Signature: %s
        Method Body:
        ```java
        %s
        ```
        
        Class: %s
        
        Generate test methods covering:
        1. Normal operation
        2. Edge cases
        3. Exception scenarios
        4. Boundary conditions
        
        Return only the test methods:
        """;
        
    private String styleAnalysisPrompt = """
        Analyze the following existing test code and extract the testing patterns and style:
        
        ```java
        %s
        ```
        
        Identify:
        1. Naming conventions
        2. Assertion styles
        3. Setup patterns
        4. Test structure
        5. Common patterns
        
        Return analysis as structured format:
        """;
} 