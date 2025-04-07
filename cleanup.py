#!/usr/bin/env python3
"""
Cleanup script for AI Scrum Master agents.
This script cleans up any running agents and temporary files.
"""

import os
import sys
import signal
import subprocess
import json
import time

def kill_processes_by_ports(ports):
    """Kill processes using the specified ports"""
    for port in ports:
        try:
            # Find process ID using the port
            cmd = f"lsof -ti:{port}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.stdout.strip():
                pid = result.stdout.strip()
                print(f"Killing process on port {port} (PID: {pid})")
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(0.5)  # Give process time to terminate
        except Exception as e:
            print(f"Error killing process on port {port}: {e}")

def kill_python_processes_by_name(pattern):
    """Kill Python processes matching a pattern"""
    try:
        # More comprehensive search for agent processes
        cmd = f"ps -ef | grep -E 'python.*{pattern}|python3.*{pattern}|src.*{pattern}|agent' | grep -v grep | awk '{{print $2}}'"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        for pid in result.stdout.strip().split('\n'):
            if pid:
                try:
                    print(f"Killing Python process with PID {pid}")
                    os.kill(int(pid), signal.SIGKILL)
                except Exception as e:
                    print(f"Error killing process {pid}: {e}")
        time.sleep(0.5)  # Give processes time to terminate
    except Exception as e:
        print(f"Error finding processes matching '{pattern}': {e}")

def clean_temp_files():
    """Clean temporary files"""
    temp_files = [
        "agent_addresses.json",
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            try:
                print(f"Removing temporary file: {file}")
                os.remove(file)
            except Exception as e:
                print(f"Error removing {file}: {e}")
    
    # Clear log file
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "agent.log")
    try:
        with open(log_file, "w") as f:
            f.write("")
        print(f"Cleared log file: {log_file}")
    except Exception as e:
        print(f"Error clearing log file {log_file}: {e}")

def main():
    print("Starting cleanup...")
    
    # Kill processes on the ports used by agents
    agent_ports = [8000, 8001, 8002, 8003, 8004, 8005]
    kill_processes_by_ports(agent_ports)
    
    # Kill Python processes related to agents
    process_patterns = ["src.deploy_agents", "src.test_agent_flow", "agent", "python.*agent", "deploy", "test_agent"]
    for pattern in process_patterns:
        kill_python_processes_by_name(pattern)
    
    # Clean temporary files
    clean_temp_files()
    
    print("Cleanup completed!")

if __name__ == "__main__":
    main() 