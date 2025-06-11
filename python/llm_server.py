#!/usr/bin/env python3
"""
LLM Server for Test Generation
Uses Hugging Face inference API with CodeGen model
"""

import argparse
import json
import logging
import os
from flask import Flask, request, jsonify
from huggingface_hub import InferenceClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = None

@app.route('/initialize-model', methods=['POST'])
def initialize_model():
    """Initialize the Hugging Face inference client"""
    global client
    try:
        hf_token = os.getenv('HF_TOKEN')
        if not hf_token:
            logger.error("HF_TOKEN environment variable not set")
            return jsonify({"error": "HF_TOKEN not configured"}), 500
        
        client = InferenceClient(token=hf_token)
        logger.info("Successfully initialized Hugging Face inference client")
        return jsonify({"status": "Model initialized successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Generate text using the Hugging Face inference API"""
    global client
    if client is None:
        logger.error("Model not initialized")
        return jsonify({"error": "Model not initialized"}), 500
    
    try:
        data = request.json
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No JSON data received"}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            logger.error("No prompt provided")
            return jsonify({"error": "No prompt provided"}), 400

        logger.info(f"Generating completion for prompt length: {len(prompt)}")
        logger.debug(f"Prompt: {prompt[:100]}...")
        
        # Generate code using a reliable smaller model
        try:
            completion = client.text_generation(
                prompt,
                model="microsoft/CodeGPT-small-java",  # Smaller, reliable model for Java
                max_new_tokens=data.get('max_tokens', 512),
                temperature=data.get('temperature', 0.7),
                top_p=data.get('top_p', 0.95),
                do_sample=True,
                return_full_text=False
            )
            logger.debug(f"Raw completion: {completion}")
        except Exception as api_error:
            logger.error(f"API error: {str(api_error)}")
            # Try with a fallback model
            try:
                logger.info("Trying fallback model...")
                completion = client.text_generation(
                    prompt,
                    model="distilgpt2",  # Simple fallback model
                    max_new_tokens=data.get('max_tokens', 256),
                    temperature=data.get('temperature', 0.7),
                    do_sample=True,
                    return_full_text=False
                )
            except Exception as fallback_error:
                logger.error(f"Fallback API error: {str(fallback_error)}")
                return jsonify({"error": f"API error: {str(api_error)}, Fallback error: {str(fallback_error)}"}), 500
        
        if not completion:
            logger.error("Empty completion received from model")
            return jsonify({"error": "Empty completion received from model"}), 500
            
        logger.info(f"Successfully generated completion of length: {len(completion)}")
        return jsonify({"response": completion}), 200
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LLM Server for Test Generation')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    args = parser.parse_args()
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info("Using CodeGPT-small-java model via Hugging Face inference API")
    
    app.run(host=args.host, port=args.port)