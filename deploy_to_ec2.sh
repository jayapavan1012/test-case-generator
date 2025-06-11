#!/bin/bash

# EC2 Deployment Script for Optimized CodeLlama Test Generator
# Usage: ./deploy_to_ec2.sh [EC2_HOST] [KEY_PATH] [GPU_FLAG]

set -e

echo "🚀 EC2 CodeLlama Test Generator Deployment"
echo "=========================================="

# Configuration
EC2_HOST=${1:-"your-ec2-instance.com"}
KEY_PATH=${2:-"~/.ssh/your-key.pem"}
USE_GPU=${3:-"false"}
REMOTE_USER="ubuntu"  # Change to your EC2 user (ubuntu/ec2-user/etc.)
REMOTE_DIR="/home/$REMOTE_USER/test-generator"
MODEL_PATH="/home/adminuser/models/codellama-13b-instruct.Q4_K_M.gguf"

if [ "$EC2_HOST" = "your-ec2-instance.com" ]; then
    echo "❌ Please provide your EC2 instance hostname/IP"
    echo "Usage: ./deploy_to_ec2.sh EC2_HOST KEY_PATH [true/false for GPU]"
    echo "Example: ./deploy_to_ec2.sh ec2-12-34-56-78.compute-1.amazonaws.com ~/.ssh/my-key.pem false"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "   EC2 Host: $EC2_HOST"
echo "   SSH Key: $KEY_PATH"
echo "   Remote User: $REMOTE_USER"
echo "   GPU Support: $USE_GPU"
echo "   Model Path: $MODEL_PATH"
echo

# Test SSH connection
echo "🔐 Testing SSH connection..."
if ! ssh -i "$KEY_PATH" -o ConnectTimeout=10 "$REMOTE_USER@$EC2_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ SSH connection failed. Please check:"
    echo "   - EC2 instance is running"
    echo "   - Security group allows SSH (port 22)"
    echo "   - SSH key path is correct"
    echo "   - SSH key permissions are correct (chmod 400)"
    exit 1
fi
echo "✅ SSH connection successful"

# Create remote directory
echo "📁 Creating remote directory structure..."
ssh -i "$KEY_PATH" "$REMOTE_USER@$EC2_HOST" "
    mkdir -p $REMOTE_DIR/python
    mkdir -p $REMOTE_DIR/logs
"

# Copy optimized CodeLlama script
echo "📤 Uploading optimized CodeLlama script..."
scp -i "$KEY_PATH" python/codellama_test_generator.py "$REMOTE_USER@$EC2_HOST:$REMOTE_DIR/python/"

# Copy requirements and setup files
echo "📤 Uploading configuration files..."
scp -i "$KEY_PATH" requirements.txt "$REMOTE_USER@$EC2_HOST:$REMOTE_DIR/" 2>/dev/null || echo "   No requirements.txt found - will install manually"

# Create EC2 setup script
cat > ec2_setup.sh << 'EOF'
#!/bin/bash
echo "🔧 Setting up CodeLlama Test Generator on EC2..."

# Update system
sudo apt-get update

# Install Python and pip if needed
sudo apt-get install -y python3 python3-pip

# Install required Python packages
pip3 install --user flask llama-cpp-python psutil

# Set up environment
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Check system resources
echo "💻 System Information:"
echo "   Total RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "   Available RAM: $(free -h | grep Mem | awk '{print $7}')"
echo "   CPU Cores: $(nproc)"
echo "   GPU: $(lspci | grep -i nvidia || echo 'No NVIDIA GPU detected')"

# Check if model exists
MODEL_PATH="/home/adminuser/models/codellama-13b-instruct.Q4_K_M.gguf"
if [ -f "$MODEL_PATH" ]; then
    echo "✅ CodeLlama model found at $MODEL_PATH"
    ls -lh "$MODEL_PATH"
else
    echo "⚠️  CodeLlama model not found at $MODEL_PATH"
    echo "   Please ensure the model is downloaded and accessible"
fi

echo "✅ EC2 setup completed!"
EOF

# Upload and run setup script
echo "📤 Uploading EC2 setup script..."
scp -i "$KEY_PATH" ec2_setup.sh "$REMOTE_USER@$EC2_HOST:$REMOTE_DIR/"
ssh -i "$KEY_PATH" "$REMOTE_USER@$EC2_HOST" "chmod +x $REMOTE_DIR/ec2_setup.sh && $REMOTE_DIR/ec2_setup.sh"

# Create server startup script
cat > start_server.sh << EOF
#!/bin/bash
cd $REMOTE_DIR

echo "🚀 Starting Optimized CodeLlama Test Generator..."
echo "   Time: \$(date)"
echo "   GPU Mode: $USE_GPU"
echo "   Model: $MODEL_PATH"

# Kill any existing server
pkill -f "python.*codellama_test_generator" || true
sleep 2

# Start server with optimized settings
nohup python3 python/codellama_test_generator.py \\
    --port 8082 \\
    --host 0.0.0.0 \\
    --model-path "$MODEL_PATH" \\
    $([ "$USE_GPU" = "true" ] && echo "--use-gpu") \\
    > logs/codellama_server.log 2>&1 &

SERVER_PID=\$!
echo "📋 Server started with PID: \$SERVER_PID"
echo "📄 Logs: $REMOTE_DIR/logs/codellama_server.log"

# Wait for server to start
echo "⏳ Waiting for server to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:8082/health > /dev/null 2>&1; then
        echo "✅ Server is running and healthy!"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        echo "📄 Check logs: tail -f $REMOTE_DIR/logs/codellama_server.log"
        exit 1
    fi
    sleep 2
done

# Display server info
echo "🎯 Server Information:"
curl -s http://localhost:8082/health | python3 -m json.tool 2>/dev/null || echo "   Health check endpoint not responding"

echo "📡 Access URLs:"
echo "   Health: http://$EC2_HOST:8082/health"
echo "   Model Info: http://$EC2_HOST:8082/model-info"
echo "   System Status: http://$EC2_HOST:8082/system-status"
echo "   Generate Tests: POST http://$EC2_HOST:8082/generate"

echo "🛑 To stop server: pkill -f 'python.*codellama_test_generator'"
echo "📊 To monitor: tail -f $REMOTE_DIR/logs/codellama_server.log"
EOF

# Upload startup script
echo "📤 Uploading server startup script..."
scp -i "$KEY_PATH" start_server.sh "$REMOTE_USER@$EC2_HOST:$REMOTE_DIR/"
ssh -i "$KEY_PATH" "$REMOTE_USER@$EC2_HOST" "chmod +x $REMOTE_DIR/start_server.sh"

# Create test script
cat > test_server.sh << EOF
#!/bin/bash
echo "🧪 Testing CodeLlama Server on EC2..."

# Test health endpoint
echo "1. Health Check:"
curl -s http://localhost:8082/health | python3 -m json.tool

echo -e "\n2. System Status:"
curl -s http://localhost:8082/system-status | python3 -m json.tool

echo -e "\n3. Model Info:"
curl -s http://localhost:8082/model-info | python3 -m json.tool

echo -e "\n4. Test Generation (Calculator):"
curl -s -X POST http://localhost:8082/generate \\
    -H "Content-Type: application/json" \\
    -d '{"prompt": "public class Calculator { public int add(int a, int b) { return a + b; } }", "className": "Calculator"}' \\
    | python3 -m json.tool

echo -e "\n✅ Testing completed!"
EOF

# Upload test script
echo "📤 Uploading test script..."
scp -i "$KEY_PATH" test_server.sh "$REMOTE_USER@$EC2_HOST:$REMOTE_DIR/"
ssh -i "$KEY_PATH" "$REMOTE_USER@$EC2_HOST" "chmod +x $REMOTE_DIR/test_server.sh"

# Clean up local files
rm -f ec2_setup.sh start_server.sh test_server.sh

echo "✅ Deployment completed successfully!"
echo
echo "🎯 Next Steps:"
echo "1. SSH to your EC2 instance:"
echo "   ssh -i $KEY_PATH $REMOTE_USER@$EC2_HOST"
echo
echo "2. Start the optimized CodeLlama server:"
echo "   cd $REMOTE_DIR && ./start_server.sh"
echo
echo "3. Test the server:"
echo "   ./test_server.sh"
echo
echo "4. Initialize the model (from your local machine):"
echo "   curl -X POST http://$EC2_HOST:8082/initialize-model \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"model_path\": \"$MODEL_PATH\", \"use_gpu\": $USE_GPU}'"
echo
echo "5. Monitor server logs:"
echo "   tail -f $REMOTE_DIR/logs/codellama_server.log"
echo
echo "📋 Key Optimizations Applied:"
echo "   ✅ 16 CPU threads (CPU mode) or 8 threads + GPU (GPU mode)"
echo "   ✅ Memory monitoring and reporting"
echo "   ✅ Result caching for faster repeated requests" 
echo "   ✅ Optimized batch processing for 32GB RAM"
echo "   ✅ Memory-mapped model loading"
echo "   ✅ Enhanced JUnit test generation prompts"
echo
echo "🚀 Your EC2 instance is ready for high-performance CodeLlama inference!" 