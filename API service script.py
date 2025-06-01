#!/usr/bin/env python3
"""
Parkin Bluetooth Lamp Control API
Usage:
    python3 parkin_api.py [--host HOST] [--port PORT]
"""

from flask import Flask, request, jsonify
import subprocess
import json
import threading
import time
from dataclasses import dataclass
from typing import Dict, List

app = Flask(__name__)

# Configuration
CONFIG_FILE = "lamp_config.json"
MESH_COMMAND_PATH = "/usr/bin/meshctl"  # BlueZ meshctl tool

# Lamp status tracking
@dataclass
class LampStatus:
    node_id: int
    color: str  # "red", "green", "purple"
    last_updated: float
    health: str  # "online", "offline", "degraded"

lamps: Dict[int, LampStatus] = {}

def load_config():
    """Load lamp configuration from file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            for lamp in config['lamps']:
                lamps[lamp['node_id']] = LampStatus(
                    node_id=lamp['node_id'],
                    color="green",
                    last_updated=time.time(),
                    health="online"
                )
    except FileNotFoundError:
        # Initialize with 100 lamps (node IDs 1-100)
        for i in range(1, 101):
            lamps[i] = LampStatus(
                node_id=i,
                color="green",
                last_updated=time.time(),
                health="online"
            )
        save_config()

def save_config():
    """Save lamp configuration to file"""
    config = {
        "lamps": [
            {
                "node_id": lamp.node_id,
                "slots": list(range((lamp.node_id-1)*6 + 1, lamp.node_id*6 + 1))
            }
            for lamp in lamps.values()
        ]
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def send_mesh_command(node_id: int, color: str):
    """Send command to Bluetooth Mesh network"""
    color_map = {
        "red": [255, 0, 0],
        "green": [0, 255, 0],
        "purple": [128, 0, 128]
    }
    
    if color not in color_map:
        return False
    
    r, g, b = color_map[color]
    
    try:
        # Using meshctl CLI tool
        cmd = [
            MESH_COMMAND_PATH,
            "send",
            str(node_id),
            "vendor",
            "1",  # Set color command
            str(r),
            str(g),
            str(b)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            lamps[node_id].color = color
            lamps[node_id].last_updated = time.time()
            return True
        else:
            lamps[node_id].health = "degraded"
            return False
    except Exception as e:
        print(f"Error sending command to node {node_id}: {str(e)}")
        lamps[node_id].health = "offline"
        return False

@app.route('/api/lamp/<int:node_id>', methods=['POST'])
def update_lamp(node_id):
    """Update single lamp color"""
    if node_id not in lamps:
        return jsonify({"status": "error", "message": "Invalid node ID"}), 404
    
    data = request.get_json()
    if not data or 'color' not in data:
        return jsonify({"status": "error", "message": "Missing color parameter"}), 400
    
    color = data['color'].lower()
    if color not in ['red', 'green', 'purple']:
        return jsonify({"status": "error", "message": "Invalid color"}), 400
    
    success = send_mesh_command(node_id, color)
    if success:
        return jsonify({"status": "success", "node_id": node_id, "color": color})
    else:
        return jsonify({"status": "error", "message": "Failed to update lamp"}), 500

@app.route('/api/lamp/bulk', methods=['POST'])
def bulk_update():
    """Bulk update multiple lamps"""
    data = request.get_json()
    if not data or 'updates' not in data:
        return jsonify({"status": "error", "message": "Missing updates"}), 400
    
    results = []
    for update in data['updates']:
        if 'node_id' not in update or 'color' not in update:
            continue
        
        node_id = update['node_id']
        color = update['color'].lower()
        
        if node_id in lamps and color in ['red', 'green', 'purple']:
            success = send_mesh_command(node_id, color)
            results.append({
                "node_id": node_id,
                "status": "success" if success else "failed",
                "color": color
            })
    
    return jsonify({"status": "completed", "results": results})

@app.route('/api/lamp/reset', methods=['POST'])
def reset_all():
    """Reset all lamps to green"""
    for node_id in lamps:
        send_mesh_command(node_id, "green")
    return jsonify({"status": "success", "message": "All lamps reset to green"})

@app.route('/api/lamp/<int:node_id>', methods=['GET'])
def get_lamp_status(node_id):
    """Get single lamp status"""
    if node_id not in lamps:
        return jsonify({"status": "error", "message": "Invalid node ID"}), 404
    
    lamp = lamps[node_id]
    return jsonify({
        "node_id": lamp.node_id,
        "color": lamp.color,
        "last_updated": lamp.last_updated,
        "health": lamp.health
    })

@app.route('/api/lamp/health', methods=['GET'])
def get_health():
    """Get system health status"""
    online = sum(1 for lamp in lamps.values() if lamp.health == "online")
    offline = sum(1 for lamp in lamps.values() if lamp.health == "offline")
    degraded = sum(1 for lamp in lamps.values() if lamp.health == "degraded")
    
    return jsonify({
        "total_lamps": len(lamps),
        "online": online,
        "offline": offline,
        "degraded": degraded
    })

def health_check_thread():
    """Periodically check lamp health"""
    while True:
        for node_id, lamp in lamps.items():
            # If not updated in last 5 minutes, mark as offline
            if time.time() - lamp.last_updated > 300:
                lamp.health = "offline"
        time.sleep(60)

if __name__ == '__main__':
    load_config()
    
    # Start health check thread
    threading.Thread(target=health_check_thread, daemon=True).start()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port)
