#!/bin/bash

# 🚀 JUnit Test Generator SDK - Demo Runner Script
# This script properly sets up the classpath and runs the demo

echo "=== Test Generator SDK Demo ==="
echo ""
echo "This demo shows how to use the Test Generator SDK in your Java applications."
echo ""

# Check if server URL is provided
SERVER_URL=${1:-"http://localhost:8080"}

echo "Using server URL: $SERVER_URL"
echo ""
echo "Note: Make sure your Test Generator server is running at the specified URL."
echo "If the server is not running, you'll see connection errors (which is expected for this demo)."
echo ""

# Build the project if not already built
if [ ! -f "build/libs/sdk-demo-1.0-SNAPSHOT-all.jar" ]; then
    echo "Building the demo project..."
    ./gradlew fatJar
    echo ""
fi

# Run the demo
echo "Running the SDK demo..."
echo "----------------------------------------"
java -Dserver.url="$SERVER_URL" -jar build/libs/sdk-demo-1.0-SNAPSHOT-all.jar

echo ""
echo "----------------------------------------"
echo "Demo completed!"
echo ""
echo "To use the SDK in your own project:"
echo "1. Copy the SDK classes from src/main/java/com/mpokket/testgenerator/sdk/"
echo "2. Add Jackson dependencies to your build.gradle/pom.xml"
echo "3. Initialize the SDK with your server URL"
echo "4. Start generating tests!"
echo ""
echo "See README.md for detailed usage instructions."

echo "🔧 Setting up demo environment..."

# Build the project first
echo "Building project..."
./gradlew build -x test -q

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Please fix compilation errors first."
    exit 1
fi

echo "✅ Build successful!"

# Get all dependency JARs from Gradle
echo "🔗 Resolving dependencies..."
GRADLE_LIBS=$(./gradlew -q printClasspath 2>/dev/null)

# If printClasspath task doesn't exist, create a simple classpath
if [ -z "$GRADLE_LIBS" ]; then
    # Create classpath manually
    CLASSPATH="build/classes/java/main"
    
    # Add Jackson libraries (most important for demo)
    JACKSON_CORE=$(find ~/.gradle/caches -name "jackson-core-*.jar" 2>/dev/null | head -1)
    JACKSON_DATABIND=$(find ~/.gradle/caches -name "jackson-databind-*.jar" 2>/dev/null | head -1)
    JACKSON_ANNOTATIONS=$(find ~/.gradle/caches -name "jackson-annotations-*.jar" 2>/dev/null | head -1)
    
    if [ -n "$JACKSON_CORE" ]; then
        CLASSPATH="$CLASSPATH:$JACKSON_CORE"
    fi
    if [ -n "$JACKSON_DATABIND" ]; then
        CLASSPATH="$CLASSPATH:$JACKSON_DATABIND"
    fi
    if [ -n "$JACKSON_ANNOTATIONS" ]; then
        CLASSPATH="$CLASSPATH:$JACKSON_ANNOTATIONS"
    fi
    
    # Add all JARs in libs directory if it exists
    if [ -d "libs" ]; then
        for jar in libs/*.jar; do
            if [ -f "$jar" ]; then
                CLASSPATH="$CLASSPATH:$jar"
            fi
        done
    fi
else
    CLASSPATH="build/classes/java/main:$GRADLE_LIBS"
fi

echo "📁 Classpath configured"

# Function to run a demo class
run_demo() {
    local CLASS_NAME=$1
    local DEMO_NAME=$2
    
    echo ""
    echo "🎬 Running: $DEMO_NAME"
    echo "=" $(printf "%*s" ${#DEMO_NAME} "" | tr ' ' '=')
    
    java -cp "$CLASSPATH" "$CLASS_NAME"
    
    if [ $? -eq 0 ]; then
        echo "✅ $DEMO_NAME completed successfully!"
    else
        echo "❌ $DEMO_NAME failed!"
        return 1
    fi
}

# Check command line arguments
if [ "$1" = "sdk" ] || [ "$1" = "" ]; then
    run_demo "com.mpokket.testgenerator.demo.SDKDemo" "SDK Demo"
elif [ "$1" = "integration" ]; then
    run_demo "com.mpokket.testgenerator.demo.QuickIntegrationExample" "Integration Examples"
elif [ "$1" = "both" ]; then
    run_demo "com.mpokket.testgenerator.demo.SDKDemo" "SDK Demo"
    echo ""
    run_demo "com.mpokket.testgenerator.demo.QuickIntegrationExample" "Integration Examples"
else
    echo "Usage: $0 [sdk|integration|both]"
    echo "  sdk         - Run the main SDK demo (default)"
    echo "  integration - Run integration examples"
    echo "  both        - Run both demos"
    exit 1
fi

echo ""
echo "🎯 Demo execution completed!" 