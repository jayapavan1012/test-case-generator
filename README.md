# Junit TestCase Generator

## Problem Statement

-   **Redundant and Repetitive Work**: Test logic often follows similar patterns, leading to repetitive manual effort across different modules.
-   **Missed Edge Cases**: Manually written tests may overlook boundary conditions or rare input scenarios, reducing reliability.
-   **Reduced Focus on Core Development**: Time spent writing tests delays feature development and impacts overall productivity.
-   **Varies by Developer Experience**: The quality and thoroughness of test cases can depend heavily on the individual developer's testing knowledge.
-   **Time-Intensive Process**: Writing unit tests from scratch takes considerable developer time, especially for complex business logic.

## Proposed Solution

-   **Integrated with Large Language Models (LLMs)**: Uses models like Ollama and DeepSeek Coder 16B to understand method logic and suggest relevant test scenarios.
-   **Custom Artifact Published to Maven Local**: The test generator is packaged as a Maven-compatible artifact and can be easily integrated into other Java projects.
-   **Simple Workflow for Developers**: Developers call the library method with a target class or method, and the tool returns ready-to-use JUnit test code.
-   **Accelerates Testing in Existing Repositories**: Designed to plug into existing service repositories.

## Technology Stack & AI Tools

-   Python (for Backend Orchestration)
-   DeepSeek Coder (6.7B / 16B models)
-   Ollama (Broker)
-   Java, Spring Boot

## Infrastructure Requirements

To run the DeepSeek Coder model effectively, the following infrastructure is recommended:
-   **RAM**: 32GB
-   **CPU**: 8 cores
-   **GPU**: 24GB VRAM

## Setup Instructions

### 1. Run the AI Model with Ollama
First, ensure Ollama is running and then pull and run the DeepSeek Coder model with the following command:
```bash
ollama run deepseek-coder-v2:16b
```

### 2. Run the Python Backend Server
Start the Python server which orchestrates the test generation. Run this on your server or EC2 instance:
```bash
python3 deepseek_coder_server.py --port 9092
```

## Usage in a Java Project

### Integrate the Dependency
To use the test generator in your Java project, add the following dependency to your build configuration. Make sure the artifact has been published to your local Maven repository.

**Gradle (`build.gradle`)**
```groovy
implementation 'com.mpokket:test-generator:1.0.0-DEEPSEEK'
```

**Maven (`pom.xml`)**
```xml
<dependency>
    <groupId>com.mpokket</groupId>
    <artifactId>test-generator</artifactId>
    <version>1.0.0-DEEPSEEK</version>
</dependency>
```

Once the dependency is integrated, you can use the test generation functionality within your project to create JUnit tests for your classes. 