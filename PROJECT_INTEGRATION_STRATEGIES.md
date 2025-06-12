# 🚀 **JUnit Test Generator - Integration Strategies Guide**

## **Overview**

You have a powerful **Deepseek-Coder-V2:16b** test generator that can be integrated into other projects in multiple ways. This guide provides **6 different integration strategies** from simple to advanced.

---

## **🎯 Integration Strategy Matrix**

| Strategy | Complexity | Best For | Setup Time | Maintenance |
|----------|------------|----------|------------|-------------|
| **1. REST API Client** | ⭐ Low | Quick integration | 10 mins | Low |
| **2. Maven/Gradle Plugin** | ⭐⭐ Medium | Build automation | 30 mins | Medium |
| **3. CLI Tool** | ⭐ Low | Command line usage | 15 mins | Low |
| **4. CI/CD Integration** | ⭐⭐⭐ Medium | Automated testing | 45 mins | Medium |
| **5. IDE Plugin** | ⭐⭐⭐⭐ High | Developer experience | 2-4 hours | High |
| **6. Library/SDK** | ⭐⭐ Medium | Custom integration | 1 hour | Medium |

---

## **🔥 Strategy 1: REST API Client Integration**

### **Use Case:** Integrate into existing projects via HTTP calls

### **Implementation Options:**

#### **Option A: Simple HTTP Client (Any Language)**

**Java Example:**
```java
// TestGeneratorClient.java
public class TestGeneratorClient {
    private final String baseUrl;
    private final RestTemplate restTemplate;
    
    public TestGeneratorClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.restTemplate = new RestTemplate();
    }
    
    public String generateTests(String javaCode, String className) {
        Map<String, Object> request = Map.of(
            "javaCode", javaCode,
            "className", className,
            "model", "auto"
        );
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                baseUrl + "/api/deepseek/generate-tests-v2",
                request,
                Map.class
            );
            
            return (String) response.getBody().get("generatedTests");
        } catch (Exception e) {
            throw new RuntimeException("Test generation failed: " + e.getMessage());
        }
    }
    
    // Usage in your project
    public static void main(String[] args) {
        TestGeneratorClient client = new TestGeneratorClient("http://localhost:8081");
        
        String javaCode = """
            public class UserService {
                public User findById(Long id) {
                    return userRepository.findById(id);
                }
            }
            """;
        
        String tests = client.generateTests(javaCode, "UserService");
        
        // Save to test file
        Files.writeString(Paths.get("src/test/java/UserServiceTest.java"), tests);
    }
}
```

**Python Example:**
```python
# test_generator_client.py
import requests
import os

class TestGeneratorClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
    
    def generate_tests(self, java_code, class_name, model="auto"):
        response = requests.post(f"{self.base_url}/api/deepseek/generate-tests-v2", 
                               json={
                                   "javaCode": java_code,
                                   "className": class_name,
                                   "model": model
                               })
        
        if response.status_code == 200:
            return response.json()["generatedTests"]
        else:
            raise Exception(f"Test generation failed: {response.text}")
    
    def generate_tests_for_file(self, java_file_path):
        with open(java_file_path, 'r') as f:
            java_code = f.read()
        
        class_name = self.extract_class_name(java_code)
        tests = self.generate_tests(java_code, class_name)
        
        # Save test file
        test_file_path = java_file_path.replace("src/main/java", "src/test/java").replace(".java", "Test.java")
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        
        with open(test_file_path, 'w') as f:
            f.write(tests)
        
        return test_file_path
    
    def extract_class_name(self, java_code):
        import re
        match = re.search(r'public\s+class\s+(\w+)', java_code)
        return match.group(1) if match else "TestClass"

# Usage
if __name__ == "__main__":
    client = TestGeneratorClient()
    
    # Generate tests for a specific file
    test_file = client.generate_tests_for_file("src/main/java/com/example/UserService.java")
    print(f"Generated test file: {test_file}")
```

---

## **🔧 Strategy 2: Maven/Gradle Plugin Integration**

### **Use Case:** Automatically generate tests during build process

### **Gradle Plugin Implementation:**

```kotlin
// buildSrc/src/main/kotlin/TestGeneratorPlugin.kt
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.TaskAction
import org.gradle.api.DefaultTask
import java.io.File
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.net.URI

class TestGeneratorPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        project.extensions.create("testGenerator", TestGeneratorExtension::class.java)
        
        project.tasks.register("generateTests", GenerateTestsTask::class.java) { task ->
            task.group = "testing"
            task.description = "Generate JUnit tests using Deepseek-Coder"
        }
    }
}

open class TestGeneratorExtension {
    var serverUrl: String = "http://localhost:8081"
    var sourceDir: String = "src/main/java"
    var testDir: String = "src/test/java"
    var model: String = "auto"
    var packageIncludes: List<String> = listOf("**/*.java")
    var packageExcludes: List<String> = listOf("**/Test*.java", "**/*Test.java")
}

open class GenerateTestsTask : DefaultTask() {
    
    @TaskAction
    fun generateTests() {
        val extension = project.extensions.getByType(TestGeneratorExtension::class.java)
        val client = TestGeneratorClient(extension.serverUrl)
        
        val sourceDir = File(project.projectDir, extension.sourceDir)
        val testDir = File(project.projectDir, extension.testDir)
        
        sourceDir.walkTopDown()
            .filter { it.isFile && it.extension == "java" }
            .filter { file -> 
                extension.packageIncludes.any { pattern -> 
                    file.relativeTo(sourceDir).path.matches(Regex(pattern.replace("**", ".*").replace("*", "[^/]*")))
                }
            }
            .filter { file ->
                extension.packageExcludes.none { pattern ->
                    file.relativeTo(sourceDir).path.matches(Regex(pattern.replace("**", ".*").replace("*", "[^/]*")))
                }
            }
            .forEach { javaFile ->
                try {
                    println("Generating tests for: ${javaFile.relativeTo(sourceDir)}")
                    
                    val javaCode = javaFile.readText()
                    val className = extractClassName(javaCode)
                    val tests = client.generateTests(javaCode, className, extension.model)
                    
                    val testFile = File(testDir, javaFile.relativeTo(sourceDir).path.replace(".java", "Test.java"))
                    testFile.parentFile.mkdirs()
                    testFile.writeText(tests)
                    
                    println("✅ Generated: ${testFile.relativeTo(testDir)}")
                } catch (e: Exception) {
                    println("❌ Failed to generate tests for ${javaFile.name}: ${e.message}")
                }
            }
    }
    
    private fun extractClassName(javaCode: String): String {
        return Regex("public\\s+class\\s+(\\w+)").find(javaCode)?.groupValues?.get(1) ?: "TestClass"
    }
}
```

**Usage in build.gradle:**
```gradle
plugins {
    id 'java'
    id 'test-generator'
}

testGenerator {
    serverUrl = "http://localhost:8081"
    sourceDir = "src/main/java"
    testDir = "src/test/java"
    model = "deepseek-v2"
    packageIncludes = ["**/service/**/*.java", "**/controller/**/*.java"]
    packageExcludes = ["**/Test*.java", "**/*Test.java", "**/config/**/*.java"]
}

// Generate tests before running tests
test.dependsOn generateTests
```

**Commands:**
```bash
# Generate tests for all source files
./gradlew generateTests

# Generate tests and run them
./gradlew test

# Clean and regenerate everything
./gradlew clean generateTests test
```

### **Maven Plugin Implementation:**

```xml
<!-- pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>com.mpokket</groupId>
            <artifactId>test-generator-maven-plugin</artifactId>
            <version>1.0.0</version>
            <configuration>
                <serverUrl>http://localhost:8081</serverUrl>
                <sourceDirectory>src/main/java</sourceDirectory>
                <testDirectory>src/test/java</testDirectory>
                <model>auto</model>
                <includes>
                    <include>**/service/**/*.java</include>
                    <include>**/controller/**/*.java</include>
                </includes>
                <excludes>
                    <exclude>**/Test*.java</exclude>
                    <exclude>**/*Test.java</exclude>
                </excludes>
            </configuration>
            <executions>
                <execution>
                    <phase>generate-test-sources</phase>
                    <goals>
                        <goal>generate</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

---

## **🖥️ Strategy 3: CLI Tool Integration**

### **Use Case:** Command-line tool for developers and scripts

### **Implementation:**

```java
// TestGeneratorCLI.java
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

@Command(name = "test-gen", description = "Generate JUnit tests using Deepseek-Coder")
public class TestGeneratorCLI implements Runnable {
    
    @Option(names = {"-s", "--server"}, description = "Test generator server URL", defaultValue = "http://localhost:8081")
    private String serverUrl;
    
    @Option(names = {"-m", "--model"}, description = "Model to use (auto, deepseek-v2, deepseek-6b, demo)", defaultValue = "auto")
    private String model;
    
    @Option(names = {"-o", "--output"}, description = "Output directory for test files", defaultValue = "src/test/java")
    private String outputDir;
    
    @Option(names = {"-r", "--recursive"}, description = "Process directories recursively")
    private boolean recursive;
    
    @Option(names = {"-v", "--verbose"}, description = "Verbose output")
    private boolean verbose;
    
    @Parameters(description = "Java source files or directories to process")
    private List<String> inputs;
    
    @Override
    public void run() {
        TestGeneratorClient client = new TestGeneratorClient(serverUrl);
        
        for (String input : inputs) {
            File inputFile = new File(input);
            
            if (inputFile.isDirectory()) {
                processDirectory(inputFile, client);
            } else if (inputFile.isFile() && input.endsWith(".java")) {
                processFile(inputFile, client);
            } else {
                System.err.println("Skipping non-Java file: " + input);
            }
        }
    }
    
    private void processDirectory(File dir, TestGeneratorClient client) {
        File[] files = dir.listFiles((d, name) -> name.endsWith(".java"));
        
        if (files != null) {
            for (File file : files) {
                processFile(file, client);
            }
        }
        
        if (recursive) {
            File[] subdirs = dir.listFiles(File::isDirectory);
            if (subdirs != null) {
                for (File subdir : subdirs) {
                    processDirectory(subdir, client);
                }
            }
        }
    }
    
    private void processFile(File javaFile, TestGeneratorClient client) {
        try {
            if (verbose) {
                System.out.println("Processing: " + javaFile.getPath());
            }
            
            String javaCode = Files.readString(javaFile.toPath());
            String className = extractClassName(javaCode);
            String tests = client.generateTests(javaCode, className, model);
            
            // Determine output path
            String relativePath = javaFile.getPath();
            if (relativePath.contains("src/main/java/")) {
                relativePath = relativePath.substring(relativePath.indexOf("src/main/java/") + 14);
            }
            
            File outputFile = new File(outputDir, relativePath.replace(".java", "Test.java"));
            outputFile.getParentFile().mkdirs();
            Files.writeString(outputFile.toPath(), tests);
            
            System.out.println("✅ Generated: " + outputFile.getPath());
            
        } catch (Exception e) {
            System.err.println("❌ Failed to process " + javaFile.getPath() + ": " + e.getMessage());
        }
    }
    
    public static void main(String[] args) {
        int exitCode = new CommandLine(new TestGeneratorCLI()).execute(args);
        System.exit(exitCode);
    }
}
```

**Usage Examples:**
```bash
# Generate tests for a single file
java -jar test-generator-cli.jar src/main/java/UserService.java

# Generate tests for all files in a directory
java -jar test-generator-cli.jar -r src/main/java/com/example/service/

# Use specific model and output directory
java -jar test-generator-cli.jar -m deepseek-v2 -o generated-tests/ src/main/java/

# Verbose mode
java -jar test-generator-cli.jar -v -r src/main/java/

# Custom server
java -jar test-generator-cli.jar -s http://production-server:8081 src/main/java/
```

---

## **🔄 Strategy 4: CI/CD Pipeline Integration**

### **Use Case:** Automated test generation in continuous integration

### **GitHub Actions Example:**

```yaml
# .github/workflows/generate-tests.yml
name: Generate and Run Tests

on:
  push:
    paths:
      - 'src/main/java/**/*.java'
  pull_request:
    paths:
      - 'src/main/java/**/*.java'

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    
    services:
      test-generator:
        image: your-registry/test-generator:latest
        ports:
          - 8081:8081
        options: --health-cmd "curl -f http://localhost:8081/api/deepseek/health" --health-interval 30s --health-timeout 10s --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      
      - name: Wait for test generator to be ready
        run: |
          timeout 60 sh -c 'until curl -f http://localhost:8081/api/deepseek/health; do sleep 5; done'
      
      - name: Find modified Java files
        id: changed-files
        uses: tj-actions/changed-files@v39
        with:
          files: |
            src/main/java/**/*.java
      
      - name: Generate tests for modified files
        if: steps.changed-files.outputs.any_changed == 'true'
        run: |
          echo "Generating tests for changed files..."
          
          for file in ${{ steps.changed-files.outputs.all_changed_files }}; do
            echo "Processing: $file"
            
            # Extract class name
            CLASS_NAME=$(grep -o "public class [A-Za-z0-9_]*" "$file" | cut -d' ' -f3)
            
            # Read Java code
            JAVA_CODE=$(cat "$file")
            
            # Generate tests
            curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
              -H "Content-Type: application/json" \
              -d "{\"javaCode\": $(echo "$JAVA_CODE" | jq -Rs .), \"className\": \"$CLASS_NAME\", \"model\": \"auto\"}" \
              -o "/tmp/response.json"
            
            # Extract generated tests
            TEST_CODE=$(jq -r '.generatedTests' /tmp/response.json)
            
            # Save to test file
            TEST_FILE=$(echo "$file" | sed 's|src/main/java|src/test/java|' | sed 's|\.java|Test.java|')
            mkdir -p "$(dirname "$TEST_FILE")"
            echo "$TEST_CODE" > "$TEST_FILE"
            
            echo "✅ Generated: $TEST_FILE"
          done
      
      - name: Run generated tests
        run: ./gradlew test
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: build/test-results/
      
      - name: Comment on PR with test results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const testResults = fs.readFileSync('build/test-results/test/TEST-*.xml', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🧪 Auto-Generated Test Results\n\nTests have been automatically generated and executed for your changes.\n\n${testResults}`
            });
```

### **Jenkins Pipeline Example:**

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        TEST_GENERATOR_URL = 'http://test-generator-service:8081'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Start Test Generator') {
            steps {
                script {
                    // Start test generator service
                    sh 'docker run -d --name test-generator -p 8081:8081 test-generator:latest'
                    
                    // Wait for service to be ready
                    sh '''
                        timeout 60 sh -c 'until curl -f ${TEST_GENERATOR_URL}/api/deepseek/health; do
                            echo "Waiting for test generator to start..."
                            sleep 5
                        done'
                    '''
                }
            }
        }
        
        stage('Generate Tests') {
            steps {
                script {
                    // Find Java files that changed
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1 HEAD | grep "src/main/java.*\\.java$" || true',
                        returnStdout: true
                    ).trim().split('\n')
                    
                    if (changedFiles[0] != '') {
                        changedFiles.each { file ->
                            echo "Generating tests for: ${file}"
                            
                            // Generate tests using the API
                            sh """
                                python3 -c "
import requests
import json
import os

# Read Java file
with open('${file}', 'r') as f:
    java_code = f.read()

# Extract class name
import re
match = re.search(r'public\\s+class\\s+(\\w+)', java_code)
class_name = match.group(1) if match else 'TestClass'

# Generate tests
response = requests.post('${TEST_GENERATOR_URL}/api/deepseek/generate-tests-v2', 
                        json={
                            'javaCode': java_code,
                            'className': class_name,
                            'model': 'auto'
                        })

if response.status_code == 200:
    generated_tests = response.json()['generatedTests']
    
    # Save to test file
    test_file = '${file}'.replace('src/main/java', 'src/test/java').replace('.java', 'Test.java')
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w') as f:
        f.write(generated_tests)
    
    print(f'✅ Generated: {test_file}')
else:
    print(f'❌ Failed to generate tests: {response.text}')
    exit(1)
"
                            """
                        }
                    } else {
                        echo "No Java files changed, skipping test generation"
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                sh './gradlew test'
            }
        }
        
        stage('Publish Results') {
            steps {
                publishTestResults testResultsPattern: 'build/test-results/test/*.xml'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: false,
                    keepAll: true,
                    reportDir: 'build/reports/tests/test',
                    reportFiles: 'index.html',
                    reportName: 'Test Report'
                ])
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'docker stop test-generator && docker rm test-generator || true'
        }
    }
}
```

---

## **🎨 Strategy 5: IDE Plugin Integration**

### **Use Case:** Seamless integration into IntelliJ IDEA/VS Code

### **IntelliJ IDEA Plugin Example:**

```kotlin
// TestGeneratorAction.kt
class TestGeneratorAction : AnAction("Generate JUnit Tests", "Generate tests using Deepseek-Coder", AllIcons.RunConfigurations.Junit) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        val psiFile = e.getData(CommonDataKeys.PSI_FILE) as? PsiJavaFile ?: return
        
        // Get the current Java class
        val selectedClass = PsiTreeUtil.findChildOfType(psiFile, PsiClass::class.java)
        if (selectedClass == null) {
            Messages.showErrorDialog("No Java class found in current file", "Error")
            return
        }
        
        // Show progress dialog
        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Generating Tests...") {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "Connecting to test generator..."
                    indicator.fraction = 0.1
                    
                    val client = TestGeneratorClient.getInstance(project)
                    val javaCode = psiFile.text
                    val className = selectedClass.name ?: "TestClass"
                    
                    indicator.text = "Generating tests with Deepseek-Coder..."
                    indicator.fraction = 0.5
                    
                    val generatedTests = client.generateTests(javaCode, className)
                    
                    indicator.text = "Creating test file..."
                    indicator.fraction = 0.8
                    
                    ApplicationManager.getApplication().invokeLater {
                        createTestFile(project, psiFile, generatedTests, className)
                    }
                    
                    indicator.fraction = 1.0
                    
                } catch (e: Exception) {
                    ApplicationManager.getApplication().invokeLater {
                        Messages.showErrorDialog("Failed to generate tests: ${e.message}", "Error")
                    }
                }
            }
        })
    }
    
    private fun createTestFile(project: Project, sourceFile: PsiJavaFile, generatedTests: String, className: String) {
        WriteCommandAction.runWriteCommandAction(project) {
            try {
                // Find test directory
                val testDir = findOrCreateTestDirectory(project, sourceFile)
                
                // Create test file
                val testFileName = "${className}Test.java"
                val testFile = testDir.findChild(testFileName) ?: testDir.createChildData(this, testFileName)
                
                // Write generated tests
                VfsUtil.saveText(testFile, generatedTests)
                
                // Open the generated test file
                FileEditorManager.getInstance(project).openFile(testFile, true)
                
                // Show notification
                NotificationGroupManager.getInstance()
                    .getNotificationGroup("TestGenerator")
                    .createNotification("Test file generated successfully", NotificationType.INFORMATION)
                    .notify(project)
                
            } catch (e: Exception) {
                Messages.showErrorDialog("Failed to create test file: ${e.message}", "Error")
            }
        }
    }
    
    override fun update(e: AnActionEvent) {
        val psiFile = e.getData(CommonDataKeys.PSI_FILE)
        e.presentation.isEnabled = psiFile is PsiJavaFile
    }
}
```

**Plugin Configuration:**
```xml
<!-- plugin.xml -->
<idea-plugin>
    <id>com.mpokket.test-generator</id>
    <name>JUnit Test Generator</name>
    <version>1.0.0</version>
    <vendor>MPokket</vendor>
    
    <description>Generate JUnit tests using Deepseek-Coder AI</description>
    
    <depends>com.intellij.modules.platform</depends>
    <depends>com.intellij.modules.java</depends>
    
    <extensions defaultExtensionNs="com.intellij">
        <applicationConfigurable instance="com.mpokket.testgen.TestGeneratorConfigurable"/>
        <notificationGroup id="TestGenerator" displayType="BALLOON"/>
    </extensions>
    
    <actions>
        <action id="TestGenerator.Generate" 
                class="com.mpokket.testgen.TestGeneratorAction" 
                text="Generate JUnit Tests" 
                description="Generate tests using Deepseek-Coder">
            <add-to-group group-id="EditorPopupMenu" anchor="last"/>
            <add-to-group group-id="ProjectViewPopupMenu" anchor="last"/>
            <keyboard-shortcut keymap="$default" first-keystroke="ctrl shift T"/>
        </action>
        
        <action id="TestGenerator.GenerateAll" 
                class="com.mpokket.testgen.GenerateAllTestsAction" 
                text="Generate Tests for Package" 
                description="Generate tests for all classes in package">
            <add-to-group group-id="ProjectViewPopupMenu" anchor="last"/>
        </action>
    </actions>
</idea-plugin>
```

### **VS Code Extension Example:**

```typescript
// extension.ts
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    
    // Command to generate tests for current file
    let generateTests = vscode.commands.registerCommand('test-generator.generateTests', async () => {
        const editor = vscode.window.activeTextEditor;
        
        if (!editor) {
            vscode.window.showErrorMessage('No active Java file');
            return;
        }
        
        const document = editor.document;
        if (document.languageId !== 'java') {
            vscode.window.showErrorMessage('Please open a Java file');
            return;
        }
        
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating JUnit tests...",
            cancellable: false
        }, async (progress) => {
            try {
                progress.report({ increment: 10, message: "Reading Java code..." });
                
                const javaCode = document.getText();
                const className = extractClassName(javaCode);
                
                progress.report({ increment: 30, message: "Connecting to Deepseek-Coder..." });
                
                const config = vscode.workspace.getConfiguration('testGenerator');
                const serverUrl = config.get<string>('serverUrl', 'http://localhost:8081');
                const model = config.get<string>('model', 'auto');
                
                const response = await axios.post(`${serverUrl}/api/deepseek/generate-tests-v2`, {
                    javaCode: javaCode,
                    className: className,
                    model: model
                });
                
                progress.report({ increment: 50, message: "Creating test file..." });
                
                const generatedTests = response.data.generatedTests;
                
                // Create test file path
                const sourceUri = document.uri;
                const testUri = getTestFileUri(sourceUri);
                
                // Ensure test directory exists
                const testDir = path.dirname(testUri.fsPath);
                if (!fs.existsSync(testDir)) {
                    fs.mkdirSync(testDir, { recursive: true });
                }
                
                // Write test file
                await vscode.workspace.fs.writeFile(testUri, Buffer.from(generatedTests));
                
                progress.report({ increment: 100, message: "Opening test file..." });
                
                // Open generated test file
                const testDocument = await vscode.workspace.openTextDocument(testUri);
                await vscode.window.showTextDocument(testDocument);
                
                vscode.window.showInformationMessage(`Test file generated: ${path.basename(testUri.fsPath)}`);
                
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to generate tests: ${error.message}`);
            }
        });
    });
    
    // Command to generate tests for entire package
    let generateAllTests = vscode.commands.registerCommand('test-generator.generateAllTests', async (uri: vscode.Uri) => {
        // Implementation for bulk generation
    });
    
    context.subscriptions.push(generateTests, generateAllTests);
}

function extractClassName(javaCode: string): string {
    const match = javaCode.match(/public\s+class\s+(\w+)/);
    return match ? match[1] : 'TestClass';
}

function getTestFileUri(sourceUri: vscode.Uri): vscode.Uri {
    const sourcePath = sourceUri.fsPath;
    const testPath = sourcePath
        .replace('/src/main/java/', '/src/test/java/')
        .replace('.java', 'Test.java');
    
    return vscode.Uri.file(testPath);
}
```

**VS Code Extension Configuration:**
```json
// package.json
{
    "name": "junit-test-generator",
    "displayName": "JUnit Test Generator",
    "description": "Generate JUnit tests using Deepseek-Coder AI",
    "version": "1.0.0",
    "engines": {
        "vscode": "^1.60.0"
    },
    "categories": ["Testing", "Other"],
    "contributes": {
        "commands": [
            {
                "command": "test-generator.generateTests",
                "title": "Generate JUnit Tests",
                "category": "Test Generator"
            },
            {
                "command": "test-generator.generateAllTests",
                "title": "Generate Tests for Package",
                "category": "Test Generator"
            }
        ],
        "menus": {
            "editor/context": [
                {
                    "command": "test-generator.generateTests",
                    "when": "resourceExtname == .java",
                    "group": "navigation"
                }
            ],
            "explorer/context": [
                {
                    "command": "test-generator.generateAllTests",
                    "when": "explorerResourceIsFolder",
                    "group": "navigation"
                }
            ]
        },
        "keybindings": [
            {
                "command": "test-generator.generateTests",
                "key": "ctrl+shift+t",
                "when": "resourceExtname == .java"
            }
        ],
        "configuration": {
            "title": "Test Generator",
            "properties": {
                "testGenerator.serverUrl": {
                    "type": "string",
                    "default": "http://localhost:8081",
                    "description": "URL of the test generator server"
                },
                "testGenerator.model": {
                    "type": "string",
                    "enum": ["auto", "deepseek-v2", "deepseek-6b", "demo"],
                    "default": "auto",
                    "description": "Model to use for test generation"
                }
            }
        }
    }
}
```

---

## **📚 Strategy 6: Library/SDK Integration**

### **Use Case:** Embed test generation directly into applications

### **Implementation:**

```java
// TestGeneratorSDK.java
public class TestGeneratorSDK {
    private final TestGeneratorClient client;
    private final TestGeneratorConfig config;
    
    public TestGeneratorSDK(TestGeneratorConfig config) {
        this.config = config;
        this.client = new TestGeneratorClient(config.getServerUrl());
    }
    
    public static class Builder {
        private String serverUrl = "http://localhost:8081";
        private String defaultModel = "auto";
        private Duration timeout = Duration.ofMinutes(2);
        private int retryAttempts = 3;
        
        public Builder serverUrl(String serverUrl) {
            this.serverUrl = serverUrl;
            return this;
        }
        
        public Builder defaultModel(String model) {
            this.defaultModel = model;
            return this;
        }
        
        public Builder timeout(Duration timeout) {
            this.timeout = timeout;
            return this;
        }
        
        public Builder retryAttempts(int attempts) {
            this.retryAttempts = attempts;
            return this;
        }
        
        public TestGeneratorSDK build() {
            TestGeneratorConfig config = new TestGeneratorConfig(serverUrl, defaultModel, timeout, retryAttempts);
            return new TestGeneratorSDK(config);
        }
    }
    
    // Fluent API for test generation
    public TestGenerationRequest forClass(String javaCode) {
        return new TestGenerationRequest(client, config, javaCode);
    }
    
    public TestGenerationRequest forFile(Path javaFilePath) throws IOException {
        String javaCode = Files.readString(javaFilePath);
        return new TestGenerationRequest(client, config, javaCode)
                .sourceFile(javaFilePath);
    }
    
    public BatchTestGeneration forPackage(Path packagePath) {
        return new BatchTestGeneration(client, config, packagePath);
    }
    
    // Health check methods
    public boolean isServerAvailable() {
        try {
            client.healthCheck();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    public ServerStatus getServerStatus() {
        return client.getServerStatus();
    }
}

// Fluent API for single test generation
public class TestGenerationRequest {
    private final TestGeneratorClient client;
    private final TestGeneratorConfig config;
    private final String javaCode;
    private String className;
    private String model;
    private Path sourceFile;
    private Path outputDirectory;
    
    public TestGenerationRequest(TestGeneratorClient client, TestGeneratorConfig config, String javaCode) {
        this.client = client;
        this.config = config;
        this.javaCode = javaCode;
        this.model = config.getDefaultModel();
    }
    
    public TestGenerationRequest className(String className) {
        this.className = className;
        return this;
    }
    
    public TestGenerationRequest model(String model) {
        this.model = model;
        return this;
    }
    
    public TestGenerationRequest sourceFile(Path sourceFile) {
        this.sourceFile = sourceFile;
        if (this.className == null) {
            this.className = extractClassNameFromFile(sourceFile);
        }
        return this;
    }
    
    public TestGenerationRequest outputDirectory(Path outputDirectory) {
        this.outputDirectory = outputDirectory;
        return this;
    }
    
    // Generate and return as string
    public String generate() throws TestGenerationException {
        try {
            return client.generateTests(javaCode, className != null ? className : extractClassName(javaCode), model);
        } catch (Exception e) {
            throw new TestGenerationException("Failed to generate tests", e);
        }
    }
    
    // Generate and save to file
    public Path generateAndSave() throws TestGenerationException, IOException {
        String generatedTests = generate();
        
        Path outputPath = determineOutputPath();
        Files.createDirectories(outputPath.getParent());
        Files.writeString(outputPath, generatedTests);
        
        return outputPath;
    }
    
    // Generate and return as structured result
    public TestGenerationResult generateWithMetadata() throws TestGenerationException {
        try {
            long startTime = System.currentTimeMillis();
            String generatedTests = generate();
            long generationTime = System.currentTimeMillis() - startTime;
            
            return TestGenerationResult.builder()
                    .generatedTests(generatedTests)
                    .className(className)
                    .model(model)
                    .generationTimeMs(generationTime)
                    .sourceFile(sourceFile)
                    .build();
                    
        } catch (Exception e) {
            throw new TestGenerationException("Failed to generate tests with metadata", e);
        }
    }
}

// Batch processing for multiple files
public class BatchTestGeneration {
    private final TestGeneratorClient client;
    private final TestGeneratorConfig config;
    private final Path packagePath;
    private final List<String> includePatterns = new ArrayList<>();
    private final List<String> excludePatterns = new ArrayList<>();
    private Path outputDirectory;
    private String model;
    private boolean parallel = true;
    
    public BatchTestGeneration include(String... patterns) {
        includePatterns.addAll(Arrays.asList(patterns));
        return this;
    }
    
    public BatchTestGeneration exclude(String... patterns) {
        excludePatterns.addAll(Arrays.asList(patterns));
        return this;
    }
    
    public BatchTestGeneration outputDirectory(Path outputDirectory) {
        this.outputDirectory = outputDirectory;
        return this;
    }
    
    public BatchTestGeneration model(String model) {
        this.model = model;
        return this;
    }
    
    public BatchTestGeneration sequential() {
        this.parallel = false;
        return this;
    }
    
    public BatchTestGenerationResult generate() throws TestGenerationException {
        try {
            List<Path> javaFiles = findJavaFiles();
            
            BatchTestGenerationResult.Builder resultBuilder = BatchTestGenerationResult.builder();
            
            if (parallel) {
                generateInParallel(javaFiles, resultBuilder);
            } else {
                generateSequentially(javaFiles, resultBuilder);
            }
            
            return resultBuilder.build();
            
        } catch (Exception e) {
            throw new TestGenerationException("Batch generation failed", e);
        }
    }
}
```

**Usage Examples:**

```java
// Example 1: Simple usage
TestGeneratorSDK sdk = new TestGeneratorSDK.Builder()
    .serverUrl("http://localhost:8081")
    .defaultModel("deepseek-v2")
    .timeout(Duration.ofMinutes(3))
    .build();

String javaCode = "public class Calculator { public int add(int a, int b) { return a + b; } }";
String tests = sdk.forClass(javaCode)
    .className("Calculator")
    .generate();

System.out.println(tests);

// Example 2: File-based generation
Path testFile = sdk.forFile(Paths.get("src/main/java/Calculator.java"))
    .model("auto")
    .outputDirectory(Paths.get("src/test/java"))
    .generateAndSave();

System.out.println("Generated: " + testFile);

// Example 3: Batch generation
BatchTestGenerationResult result = sdk.forPackage(Paths.get("src/main/java/com/example/service"))
    .include("**/*Service.java", "**/*Controller.java")
    .exclude("**/*Test.java", "**/Abstract*.java")
    .model("deepseek-v2")
    .outputDirectory(Paths.get("src/test/java"))
    .generate();

System.out.println("Generated " + result.getSuccessCount() + " test files");
result.getFailures().forEach(failure -> 
    System.err.println("Failed: " + failure.getSourceFile() + " - " + failure.getError()));

// Example 4: Advanced usage with metadata
TestGenerationResult result = sdk.forClass(javaCode)
    .className("UserService")
    .model("deepseek-v2")
    .generateWithMetadata();

System.out.println("Generated tests in " + result.getGenerationTimeMs() + "ms");
System.out.println("Model used: " + result.getModelUsed());
System.out.println("Test count: " + result.getTestMethodCount());
```

---

## **🔗 Integration Recommendations**

### **For Small Projects:** 
- Use **Strategy 1 (REST API Client)** for quick integration
- Add a simple script in your project to generate tests on demand

### **For Medium Projects:**
- Use **Strategy 2 (Maven/Gradle Plugin)** for automated build integration
- Combine with **Strategy 3 (CLI Tool)** for developer convenience

### **For Large Enterprise Projects:**
- Use **Strategy 4 (CI/CD Integration)** for automated testing in pipelines
- Consider **Strategy 5 (IDE Plugin)** for developer productivity
- Use **Strategy 6 (Library/SDK)** for custom integrations

### **For Teams:**
- Start with **REST API Client** for immediate value
- Gradually adopt **CI/CD Integration** for automation
- Consider **IDE Plugin** for developer experience

---

## **🚀 Quick Start Guide**

### **1. Start Your Test Generator Server:**
```bash
# Start Spring Boot application
./gradlew bootRun

# Or start Python server directly
python3 deepseek_coder_server.py --port 9092
```

### **2. Choose Your Integration Strategy:**
```bash
# Strategy 1: REST API (quickest)
curl -X POST http://localhost:8081/api/deepseek/generate-tests-v2 \
  -H "Content-Type: application/json" \
  -d '{"javaCode": "...", "className": "Calculator", "model": "auto"}'

# Strategy 3: CLI Tool
java -jar test-generator-cli.jar src/main/java/Calculator.java
```

### **3. Scale Up:**
- Add to your build process (Strategy 2)
- Integrate into CI/CD (Strategy 4)
- Create team tools (Strategy 5 & 6)

This comprehensive integration guide provides multiple pathways to incorporate your powerful test generator into any project, from simple scripts to enterprise-grade solutions! 🎯 