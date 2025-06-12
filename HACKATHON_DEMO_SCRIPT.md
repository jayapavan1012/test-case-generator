# 🚀 **Hackathon Demo Script - JUnit Test Generator SDK**

## **🎯 Demo Objectives**
1. **Show ease of integration** - How simple it is to add to any Java project
2. **Demonstrate multiple usage patterns** - String, file, batch processing
3. **Live test generation** - Real AI-powered test creation
4. **Professional SDK design** - Builder pattern, fluent API, error handling

---

## **📋 Pre-Demo Setup (5 minutes)**

### **1. Start Your Test Generator Server**
```bash
# Terminal 1: Start the Python server
cd /home/jayapavan/Documents/Hackathon/test-generator
python3 deepseek_coder_server.py --port 8080

# Wait for server to start and show:
# ✅ Deepseek-Coder-V2:16b available
# 🌐 Server starting on 0.0.0.0:8080
```

### **2. Compile the SDK**
```bash
# Terminal 2: Build the project
./gradlew build

# Should see:
# BUILD SUCCESSFUL
```

### **3. Verify Files Are Ready**
```bash
ls -la *.java
# Should show: Calculator.java, SimpleTestService.java
```

---

## **🎬 Live Demo Execution (10-15 minutes)**

### **Demo 1: Quick Server Check (1 minute)**
```bash
# Show server is running
curl -s http://localhost:8080/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "server": "AWS g5.2xlarge (24GB A10G + 32GB RAM + 8 vCPUs)",
#   "models": {
#     "deepseek-v2": {
#       "status": "available",
#       "name": "Deepseek-Coder-V2:16b"
#     }
#   }
# }
```

### **Demo 2: Run Full SDK Demo (8 minutes)**
```bash
# Run the comprehensive demo
java -cp build/classes/java/main:build/libs/* com.mpokket.testgenerator.demo.SDKDemo

# This will show:
# 🚀 JUnit Test Generator SDK - Hackathon Demo
# ============================================================
# 
# 📊 Demo 1: Server Status Check
# ----------------------------------------
# Server Available: ✅ Yes
# Server Info: AWS g5.2xlarge (24GB A10G + 32GB RAM + 8 vCPUs)
# Version: Multi-Model Production v1.2-debug
# 
# 🔧 Demo 2: Simple Test Generation
# ----------------------------------------
# Generating tests for Calculator class...
# ✅ Generated tests successfully!
# [Generated test code preview]
# 
# 📁 Demo 3: File-based Generation
# ----------------------------------------
# Generating tests for Calculator.java...
# ✅ Generated: demo-tests/CalculatorTest.java
# 
# 🎯 Demo 4: Advanced Generation with Metadata
# ----------------------------------------
# ✅ Advanced generation completed!
# Metadata:
#   Class: UserService
#   Model: deepseek-v2
#   Generation Time: 1247 ms
#   Test Methods: 4
#   Input Length: 1156 characters
# 
# 📦 Demo 5: Batch Processing
# ----------------------------------------
# ✅ Batch generation completed!
# BATCH TEST GENERATION SUMMARY
# ============================================================
# Total Files: 2
# Successful: 2 (100.0%)
# Failed: 0
# Mode: Parallel
# Total Test Methods: 8
# 
# 🔀 Demo 6: Model Comparison
# ----------------------------------------
# Testing with model: auto
#   ✅ auto: 3 tests in 891 ms
# Testing with model: deepseek-v2
#   ✅ deepseek-v2: 3 tests in 1205 ms
```

### **Demo 3: Show Generated Files (2 minutes)**
```bash
# Show what was actually generated
echo "📁 Generated test files:"
find demo-tests batch-tests -name "*.java" 2>/dev/null || echo "Check generated files..."

# Show a sample generated test
echo -e "\n📄 Sample Generated Test:"
head -20 demo-tests/CalculatorTest.java 2>/dev/null || echo "Will be generated during demo"
```

### **Demo 4: Quick Integration Example (3 minutes)**
```bash
# Show how easy it is to integrate
java -cp build/classes/java/main:build/libs/* com.mpokket.testgenerator.demo.QuickIntegrationExample

# This demonstrates:
# 🔗 Quick Integration Examples
# ==================================================
# 
# 1️⃣  Project Integration:
# Generated JUnit tests:
# [Shows complete PaymentService test with mocks]
# 
# 2️⃣  CI/CD Integration:
# [Shows automated pipeline integration]
# 
# 3️⃣  Developer Workflow:
# ✅ Tests generated for new feature!
```

---

## **🎤 Demo Script & Talking Points**

### **Opening (30 seconds)**
> "Hi everyone! I'm excited to show you our **JUnit Test Generator SDK** - a powerful tool that makes test generation **as easy as adding one dependency** to your project. This leverages **Deepseek-Coder-V2** AI to generate comprehensive JUnit tests automatically."

### **Server Demo (1 minute)**
> "First, let me show you our **production-ready server** running on AWS with **24GB GPU**. As you can see, we have **Deepseek-Coder-V2:16b** model available and ready."

**[Run server status check]**

### **SDK Features Demo (6 minutes)**
> "Now let's see the SDK in action. Our SDK provides **three main integration patterns**:"

#### **1. Simple String-Based Generation**
> "**First - Direct code generation**. You just pass in Java code as a string, and get back complete JUnit tests. Perfect for **code review tools** or **IDE plugins**."

#### **2. File-Based Processing**
> "**Second - File-based processing**. Point it at your Java files, and it automatically generates corresponding test files with proper package structure."

#### **3. Batch Processing**
> "**Third - Batch processing**. Process entire directories in parallel. Perfect for **CI/CD pipelines** or when you want to generate tests for your whole codebase."

**[Run main demo]**

### **Integration Examples (3 minutes)**
> "But here's the real power - **integration is incredibly simple**. Let me show you how you'd actually use this in your projects:"

**[Run integration examples]**

> "As you can see, it's just **3 lines of code** to add test generation to any Java project:
> 1. Create the SDK
> 2. Call the fluent API
> 3. Get your tests
> 
> You can integrate this into **build tools**, **CI/CD pipelines**, **IDEs**, or use it as a **standalone library**."

### **Closing (30 seconds)**
> "What makes this special is the **combination of powerful AI** with **professional SDK design**. You get **production-quality test generation** with **enterprise-grade integration patterns**. 
> 
> This isn't just a demo - it's a **real SDK** you can use in **production today**."

---

## **🛠️ Troubleshooting**

### **If Server Not Running:**
```bash
# Quick fix
python3 deepseek_coder_server.py --port 8080 &
sleep 5
```

### **If Build Fails:**
```bash
# Clean and rebuild
./gradlew clean build
```

### **If Demo Files Missing:**
```bash
# The demo will work without external files
# It has embedded code examples
```

### **If Network Issues:**
```bash
# Change server URL in demo
# Edit SDKDemo.java line 29:
# .serverUrl("http://localhost:8080")
```

---

## **🎯 Key Demo Success Metrics**

### **✅ Must Show:**
1. **Server is running and healthy**
2. **AI generates real, compilable JUnit tests**
3. **Multiple integration patterns work**
4. **Professional API design** (fluent interface, builder pattern)
5. **Real file generation** with proper structure

### **💡 Talking Points to Emphasize:**
- **Production ready** - Real AWS deployment
- **Professional SDK** - Not just a script
- **Multiple models** - Deepseek-Coder-V2, fallbacks
- **Easy integration** - 3 lines of code
- **Enterprise features** - Batch processing, metadata, error handling

### **📊 Expected Demo Results:**
- **Server health check**: ✅ Available
- **Simple generation**: 2-3 test methods in ~1-2 seconds
- **File generation**: Actual `.java` test files created
- **Batch processing**: Multiple files processed in parallel
- **Integration examples**: All 3 patterns working

---

## **🚀 Post-Demo Q&A Prep**

### **Likely Questions & Answers:**

**Q: "How accurate are the generated tests?"**
> A: "The tests include proper mocking, assertions, and edge cases. Deepseek-Coder-V2 is specifically trained on code patterns and generates production-quality tests."

**Q: "Can this integrate with our existing CI/CD?"**
> A: "Absolutely! We showed 3 integration patterns. It works with Gradle, Maven, Jenkins, GitHub Actions - any environment that can call Java APIs."

**Q: "What about performance at scale?"**
> A: "The SDK supports parallel processing and we're running on AWS with 24GB GPU. It can handle enterprise workloads."

**Q: "How do you handle different code styles?"**
> A: "Deepseek-Coder-V2 understands various Java patterns - Spring, plain Java, different architectures. It adapts to your coding style."

This demo script ensures you'll have a **smooth, professional presentation** that showcases the real power and usability of your test generator! 🎯 