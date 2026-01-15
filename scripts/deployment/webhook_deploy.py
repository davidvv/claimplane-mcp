#!/usr/bin/env python3
"""
GitHub Webhook Deployment Receiver
Listens for push events from GitHub and triggers deployment
"""

import os
import hmac
import hashlib
import subprocess
import logging
from flask import Flask, request, jsonify

# Configuration
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
DEPLOY_SCRIPT = os.path.join(os.path.dirname(__file__), 'deploy.sh')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 9000))

if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable must be set")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False

    # GitHub sends signature as "sha256=<hash>"
    if not signature_header.startswith('sha256='):
        return False

    expected_signature = signature_header.split('=')[1]

    # Calculate HMAC
    mac = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    )
    calculated_signature = mac.hexdigest()

    # Compare signatures (constant time to prevent timing attacks)
    return hmac.compare_digest(calculated_signature, expected_signature)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'webhook-deploy'}), 200


@app.route('/deploy', methods=['POST'])
def deploy():
    """Handle GitHub webhook and trigger deployment"""

    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        logger.warning(f"Invalid signature from {request.remote_addr}")
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse payload
    payload = request.json

    # Check if it's a push event to MVP branch
    if payload.get('ref') != 'refs/heads/MVP':
        logger.info(f"Ignoring push to branch: {payload.get('ref')}")
        return jsonify({'message': 'Ignoring non-MVP branch'}), 200

    # Log the deployment trigger
    pusher = payload.get('pusher', {}).get('name', 'unknown')
    commits = len(payload.get('commits', []))
    logger.info(f"Deployment triggered by {pusher} ({commits} commits)")

    # Run deployment script
    try:
        logger.info("Starting deployment script...")
        result = subprocess.run(
            ['bash', DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info("Deployment completed successfully")
            return jsonify({
                'status': 'success',
                'message': 'Deployment completed successfully',
                'output': result.stdout
            }), 200
        else:
            logger.error(f"Deployment failed: {result.stderr}")
            return jsonify({
                'status': 'error',
                'message': 'Deployment failed',
                'error': result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        logger.error("Deployment script timed out")
        return jsonify({
            'status': 'error',
            'message': 'Deployment timed out'
        }), 500
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    logger.info(f"Starting webhook receiver on port {WEBHOOK_PORT}")
    logger.info(f"Deploy script: {DEPLOY_SCRIPT}")
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)
