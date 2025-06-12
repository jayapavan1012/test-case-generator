#!/bin/bash

echo "🚀 Setting up Deepseek-Coder 6.7B on Amazon Linux EC2 Distm1"
echo "============================================================="

# Update system (Amazon Linux)
echo "📦 Updating system packages..."
sudo yum update -y

# Install dependencies (Amazon Linux)
echo "🔧 Installing dependencies..."
sudo yum install -y python3 python3-pip wget curl htop git

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --user flask llama-cpp-python psutil huggingface-hub

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Create directories
echo "📁 Creating directories..."
mkdir -p /home/adminuser/models
mkdir -p /home/adminuser/logs

# Download Deepseek-Coder model
echo "📥 Downloading Deepseek-Coder 6.7B model (~4.2GB)..."
cd /home/adminuser/models

# Using huggingface-hub (more reliable)
python3 -c "
from huggingface_hub import hf_hub_download
print('Starting download...')
hf_hub_download(
    repo_id='TheBloke/deepseek-coder-6.7B-instruct-GGUF',
    filename='deepseek-coder-6.7b-instruct.Q4_K_M.gguf',
    local_dir='/home/adminuser/models',
    local_dir_use_symlinks=False
)
print('Download completed!')
"

# Verify download
echo "✅ Verifying download..."
ls -lh /home/adminuser/models/

echo ""
echo "🎉 Setup completed!"
echo "📝 Next steps:"
echo "1. Copy deepseek_coder_server.py to /home/adminuser/"
echo "2. Run: chmod +x /home/adminuser/deepseek_coder_server.py"
echo "3. Start server: nohup python3 /home/adminuser/deepseek_coder_server.py --port 8082 --host 0.0.0.0 --model-path /home/adminuser/models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf > /home/adminuser/logs/deepseek-coder.log 2>&1 &" 