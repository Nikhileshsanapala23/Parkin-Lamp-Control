# Parkin Smart Parking System

![Parkin System Overview](https://i.imgur.com/JKQ4W8x.png)  
*Visualization of the Parkin parking monitoring system*

## Table of Contents
- [System Overview](#system-overview)
- [Key Features](#key-features)
- [Hardware Requirements](#hardware-requirements)
- [Software Components](#software-components)
- [Quick Start Guide](#quick-start-guide)
- [API Documentation](#api-documentation)
- [Firmware Details](#firmware-details)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## System Overview
The Parkin system uses 100 Bluetooth-enabled RGB lamps to display real-time occupancy status of 600 parking slots (6 slots per lamp). The system consists of:

1. **Camera System** (Existing): Monitors individual parking slots
2. **Central Server** (Existing): Processes occupancy data
3. **Bluetooth Gateway**: Raspberry Pi/ESP32 running control API
4. **Lamp Nodes**: nRF52840 devices in Bluetooth mesh network

## Key Features
- 🚦 Real-time color status (Red=Occupied, Green=Vacant, Purple=Reserved)
- 📶 Bluetooth Mesh network for reliable communication
- 🖥️ Web dashboard for centralized control
- ⚡ Bulk operations (update all, reset, test modes)
- 📊 Health monitoring of all nodes

## Hardware Requirements
| Component | Specification |
|-----------|---------------|
| Gateway   | Raspberry Pi 4 or ESP32 |
| Lamp Nodes| nRF52840 MCU with RGB LED |
| Network   | Bluetooth 5.0+ |

## Software Components
| Component | Technology |
|-----------|------------|
| Firmware  | Zephyr RTOS |
| API       | Python Flask |
| Dashboard | HTML5/JavaScript |

## Quick Start Guide

### 1. Flash Firmware
```bash
nrfjprog --program firmware/parkin_v1.0.bin --sectorerase --reset -f nrf52
2. Set Up Gateway
bash
# On Raspberry Pi
sudo apt update
sudo apt install bluez python3-pip
pip3 install -r api/requirements.txt
3. Start the API
bash
python3 api/parkin_api.py --host 0.0.0.0 --port 5000
4. Access Dashboard
Open in browser:
http://[GATEWAY_IP]:5000/static/index.html

API Documentation
Endpoints
Endpoint	Method	Description
/api/lamp/<id>	POST	Update single lamp
/api/lamp/bulk	POST	Bulk update lamps
/api/lamp/health	GET	System health status
Example Request:

bash
curl -X POST http://localhost:5000/api/lamp/1 \
  -H "Content-Type: application/json" \
  -d '{"color": "green"}'
Firmware Details
Base RTOS: Zephyr 3.2

Bluetooth Stack: Nordic SoftDevice

Power Consumption: < 5mA in operation

Build instructions:

bash
west build -b nrf52840dk_nrf52840
Deployment
For production deployment:

bash
# Install as system service
sudo cp config/parkin.service /etc/systemd/system/
sudo systemctl enable parkin
sudo systemctl start parkin
Troubleshooting
Issue	Solution
Lamp not responding	Check mesh network provisioning
API connection failed	Verify gateway Bluetooth service is running
Color inconsistency	Reset lamp and reprovision
