package com.example.test;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class SimpleTestService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    private final ObjectMapper objectMapper;
    
    public SimpleTestService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }
    
    public String methodOne() {
        return "test1";
    }
    
    public boolean methodTwo(String input) {
        return input != null;
    }
    
    public void methodThree() {
        // void method
    }
    
    public int methodFour(int a, int b) {
        return a + b;
    }
    
    public String methodFive() throws Exception {
        return "test5";
    }
} 