package com.mpokket.testgenerator.service;

import java.util.List;
import java.util.Map;

/**
 * Service interface for interacting with Local Language Models (LLM)
 * for automated test case generation
 */
public interface LLMService {
    
    /**
     * Generate JUnit test cases for a given Java class
     * 
     * @param javaCode The source code to generate tests for
     * @param className The name of the class
     * @param existingTestStyle Optional existing test style to match
     * @return Generated test code as a string
     */
    String generateTestCases(String javaCode, String className, String existingTestStyle);
    
    /**
     * Generate test cases for a specific method
     * 
     * @param methodSignature The method signature
     * @param methodBody The method implementation
     * @param className The containing class name
     * @return Generated test methods
     */
    List<String> generateMethodTests(String methodSignature, String methodBody, String className);
    
    /**
     * Analyze existing test patterns from a codebase
     * 
     * @param existingTests List of existing test files
     * @return Extracted test patterns and styles
     */
    Map<String, Object> analyzeTestPatterns(List<String> existingTests);
    
    /**
     * Check if the LLM model is loaded and ready
     * 
     * @return true if model is ready, false otherwise
     */
    boolean isModelReady();
    
    /**
     * Initialize and load the LLM model
     * 
     * @return true if successful, false otherwise
     */
    boolean initializeModel();
} 