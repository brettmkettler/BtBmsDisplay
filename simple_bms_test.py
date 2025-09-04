#!/usr/bin/env python3

import subprocess
import time
import sys

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_bluetooth_basic():
    """Test basic Bluetooth functionality"""
    print("Testing basic Bluetooth...")
    
    # Check if hci0 is up
    success, output, error = run_command("hciconfig hci0")
    if not success:
        print("✗ Bluetooth adapter not found")
        return False
    
    if "UP RUNNING" in output:
        print("✓ Bluetooth adapter is UP and RUNNING")
    else:
        print("⚠ Bluetooth adapter may not be running properly")
        print(output)
    
    return True

def scan_for_bms_devices():
    """Scan for BMS devices using hcitool"""
    print("\nScanning for BLE devices with hcitool...")
    
    target_macs = ["A4:C1:38:7C:2D:F0", "E0:9F:2A:E4:94:1D"]
    
    # Start LE scan
    success, output, error = run_command("timeout 15s sudo hcitool lescan")
    
    if not success:
        print(f"✗ Scan failed: {error}")
        return []
    
    found_devices = []
    lines = output.strip().split('\n')
    
    print(f"Scan results:")
    for line in lines:
        if line and not line.startswith("LE Scan"):
            parts = line.split()
            if len(parts) >= 1:
                mac = parts[0].upper()
                name = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"
                
                if mac in [m.upper() for m in target_macs]:
                    found_devices.append((mac, name))
                    print(f"🎯 TARGET FOUND: {mac} - {name}")
                else:
                    print(f"   {mac} - {name}")
    
    return found_devices

def test_gatttool_connection(mac):
    """Test connection using gatttool"""
    print(f"\nTesting gatttool connection to {mac}...")
    
    # Try to connect and list services
    cmd = f"timeout 10s gatttool -b {mac} --primary"
    success, output, error = run_command(cmd)
    
    if success and output.strip():
        print(f"✓ Connected to {mac}")
        print("Services found:")
        for line in output.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
        return True
    else:
        print(f"✗ Connection failed: {error}")
        return False

def main():
    print("Simple BMS Connection Test")
    print("=" * 40)
    
    # Test basic Bluetooth
    if not test_bluetooth_basic():
        print("❌ Basic Bluetooth test failed")
        return
    
    # Scan for devices
    found_devices = scan_for_bms_devices()
    
    if not found_devices:
        print("\n❌ No target BMS devices found!")
        print("Devices may be:")
        print("  - Powered off")
        print("  - Out of range") 
        print("  - Already connected to another device")
        print("  - In sleep mode")
        return
    
    print(f"\n✓ Found {len(found_devices)} target device(s)")
    
    # Test connections
    for mac, name in found_devices:
        success = test_gatttool_connection(mac)
        if success:
            print(f"✅ {mac} ({name}) is accessible")
        else:
            print(f"❌ {mac} ({name}) connection failed")

if __name__ == "__main__":
    main()
