# 🚀 Deepseek-Coder 6.7B Test Generator

A high-performance Spring Boot application for generating JUnit 5 test cases using **Deepseek-Coder 6.7B-Instruct** model, optimized for EC2 deployment with 32GB RAM.

## 🎯 Overview

This application leverages the powerful Deepseek-Coder 6.7B model (Q4_K_M quantization) to automatically generate comprehensive JUnit 5 test cases for Java classes. Deployed on EC2 instance `Distm1 (10.5.17.187)` with optimized memory configuration.

## ✨ Features

- **🧠 AI-Powered**: Uses Deepseek-Coder 6.7B-Instruct for intelligent test generation
- **⚡ Optimized**: Q4_K_M quantization for 32GB RAM EC2 instances
- **🚀 Fast**: 10-45 seconds typical generation time
- **🎯 Specialized**: Specifically tuned for Java JUnit 5 test generation
- **🌐 RESTful API**: Clean REST endpoints with JSON/text support
- **💾 Caching**: Built-in caching for improved performance
- **📊 Monitoring**: System status and health endpoints
- **🔄 CORS Support**: Cross-origin requests enabled

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Client App    │───▶│  Spring Boot API │───▶│ Deepseek-Coder 6.7B│
│                 │    │  (Port 8081)     │    │ (10.5.17.187:8082) │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 📦 Tech Stack

- **Framework**: Spring Boot 3.2.3
- **Language**: Java 17
- **AI Model**: Deepseek-Coder 6.7B-Instruct (Q4_K_M)
- **Test Framework**: JUnit 5
- **Build Tool**: Gradle 8.2
- **Server**: EC2 Distm1 (32GB RAM)

## 🚀 Quick Start

### Prerequisites
- Java 17+
- Gradle 8.2+
- 32GB RAM (recommended)
- Access to Deepseek-Coder server at `10.5.17.187:8082`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd test-generator
   ```

2. **Build the application**
   ```bash
   ./gradlew clean build
   ```

3. **Run the application**
   ```bash
   ./gradlew bootRun
   ```

4. **Verify installation**
   ```bash
   curl http://localhost:8081/api/deepseek/test
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:8081/api/deepseek
```

### Endpoints

#### 🧪 Test Status
```http
GET /api/deepseek/test
```
Returns API status and available endpoints.

#### 💓 Health Check
```http
GET /api/deepseek/health
```
Returns model status and system health.

#### 🔧 Initialize Model
```http
POST /api/deepseek/initialize
```
Initializes the Deepseek-Coder model.

#### 📝 Generate Tests (JSON)
```http
POST /api/deepseek/generate-tests
Content-Type: application/json

{
  "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
  "className": "Calculator"
}
```

#### 📝 Generate Tests (Text)
```http
POST /api/deepseek/generate
Content-Type: text/plain

public class Calculator { 
  public int add(int a, int b) { 
    return a + b; 
  } 
}
```

#### 📊 System Status
```http
GET /api/deepseek/system-status
```
Returns system metrics and resource usage.

#### 🧹 Clear Cache
```http
POST /api/deepseek/clear-cache
```
Clears the generation cache.

## 🧪 Testing

### Run the test script
```bash
./test-api.sh
```

### Manual testing examples

**Basic test generation:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "javaCode": "public class Calculator { public int add(int a, int b) { return a + b; } }",
    "className": "Calculator"
  }' \
  http://localhost:8081/api/deepseek/generate-tests
```

**Health check:**
```bash
curl http://localhost:8081/api/deepseek/health
```

## ⚙️ Configuration

### Key Configuration (application.properties)

```properties
# Server
server.port=8081

# Deepseek-Coder Configuration
deepseek.coder.server.url=http://10.5.17.187:8082
deepseek.coder.timeout.seconds=120
deepseek.coder.max.retries=3

# Model Settings
deepseek.coder.model.name=Deepseek-Coder 6.7B-Instruct
deepseek.coder.model.quantization=Q4_K_M
deepseek.coder.model.context.window=8192
```

## 🔧 Deployment

### EC2 Deployment
1. Deploy to EC2 instance `Distm1 (10.5.17.187)`
2. Ensure 32GB RAM available
3. Configure Deepseek-Coder server on port 8082
4. Run with production profile:
   ```bash
   java -jar build/libs/test-generator-1.0.0-DEEPSEEK.jar --spring.profiles.active=production
   ```

### Docker Deployment
```bash
./gradlew bootBuildImage
docker run -p 8081:8081 test-generator:1.0.0-DEEPSEEK
```

## 📊 Performance

- **Generation Time**: 10-45 seconds typical
- **Context Window**: 8K tokens
- **Memory Usage**: Optimized for 32GB RAM
- **Model Size**: 6.7B parameters (Q4_K_M quantization)
- **Concurrent Requests**: Up to 20 (configurable)

## 🛠️ Development

### Build tasks
```bash
# Clean build
./gradlew clean build

# Run tests
./gradlew test

# Run with dev profile
./gradlew bootRun --args='--spring.profiles.active=dev'

# Build for deployment
./gradlew deployDeepSeekCoder
```

### Project Structure
```
src/
├── main/
│   ├── java/com/mpokket/testgenerator/
│   │   ├── controller/DeepSeekTestController.java
│   │   ├── service/DeepSeekCoderService.java
│   │   └── TestGeneratorApplication.java
│   └── resources/
│       └── application.properties
└── test/
    └── java/com/mpokket/testgenerator/
```

## 🔍 Monitoring

### Health Endpoints
- `/api/deepseek/health` - Model and system health
- `/api/deepseek/system-status` - Resource usage metrics

### Logging
Logs are available in `logs/test-generator.log` with the following levels:
- INFO: General application flow
- ERROR: Error conditions
- DEBUG: Detailed debugging information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the logs: `tail -f logs/test-generator.log`
2. Verify EC2 connectivity: `curl http://10.5.17.187:8082/health`
3. Check system resources: `curl http://localhost:8081/api/deepseek/system-status`

## 🔗 Related Links

- [Deepseek-Coder Documentation](https://github.com/deepseek-ai/deepseek-coder)
- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [JUnit 5 Documentation](https://junit.org/junit5/docs/current/user-guide/)

---

**🌟 Powered by Deepseek-Coder 6.7B-Instruct | Optimized for EC2 | Built with Spring Boot** 