package com.mpokket.testgenerator.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
// Commented out to disable this service in favor of CodeLlamaService
// import org.springframework.beans.factory.annotation.Value;
// import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * Legacy implementation of LLMService (DISABLED)
 * Replaced by CodeLlamaService for better CodeLlama 13B integration
 */
// @Service - DISABLED
@Slf4j
public class LLMServiceImpl_Legacy {

    // Legacy implementation kept for reference but disabled
    // All functionality moved to CodeLlamaService
} 