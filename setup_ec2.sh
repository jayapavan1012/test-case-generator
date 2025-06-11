#!/bin/bash

echo "Setting up CodeLlama 13B on EC2 instance..."

# Update the system
sudo yum update -y

# Install Python 3.11 and pip
sudo yum install -y python3.11 python3.11-pip git wget

# Install build tools for llama-cpp-python
sudo yum groupinstall -y "Development Tools"
sudo yum install -y cmake

# Create alias for python3.11
echo 'alias python3=/usr/bin/python3.11' >> ~/.bashrc
echo 'alias pip3=/usr/bin/pip3.11' >> ~/.bashrc
source ~/.bashrc

# Install Python packages
/usr/bin/pip3.11 install --user flask==3.0.0
/usr/bin/pip3.11 install --user llama-cpp-python --no-cache-dir

# Create models directory
mkdir -p ~/models

# Download CodeLlama 13B GGUF model (quantized for efficiency)
echo "Downloading CodeLlama 13B model..."
cd ~/models
wget -O codellama-13b-instruct.Q4_K_M.gguf "https://huggingface.co/TheBloke/CodeLlama-13B-Instruct-GGUF/resolve/main/codellama-13b-instruct.Q4_K_M.gguf"

echo "Setup complete!"
echo "Model downloaded to: ~/models/codellama-13b-instruct.Q4_K_M.gguf" 