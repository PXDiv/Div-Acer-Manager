# DAMFC_HardwareStatus v0.1.2
import psutil
import subprocess
import re

def get_cpu_temp():
    """Get CPU temperature using psutil and round to an integer."""
    try:
        sensors = psutil.sensors_temperatures()
        if "coretemp" in sensors:  # Intel & AMD CPUs
            return int(round(sensors["coretemp"][0].current))
        return None  # Return None if temperature is unavailable
    except AttributeError:
        return None

def get_gpu_temp():
    """Get NVIDIA GPU temperature using nvidia-smi."""
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            text=True
        )
        return int(output.strip())
    except Exception:
        return "N/A"

def get_fan_speed():
    """Get fan speeds using lm-sensors."""
    try:
        output = subprocess.check_output(["sensors"], text=True)
        fan_speeds = re.findall(r"(\d+)\s*RPM", output)  # Extract RPM values
        return ", ".join(fan_speeds) if fan_speeds else "No fans detected"
    except Exception:
        return "N/A"
    
def get_cpu_fan_speed():
    """Extracts the CPU fan speed from lm-sensors output."""
    try:
        output = subprocess.check_output(["sensors"], text=True)

        # Match lines containing "CPU" or the first available fan as fallback
        fan_speeds = re.findall(r"(.+?):\s+(\d+)\s*RPM", output)

        for label, speed in fan_speeds:
            if "cpu" in label.lower() or "fan1" in label.lower():  # Common labels for CPU fans
                return int(speed)

        # If CPU label isn't found, return the first available fan speed
        return int(fan_speeds[0][1]) if fan_speeds else None
    except Exception:
        return None

def get_gpu_fan_speed():
    """Extracts the GPU fan speed from lm-sensors output."""
    try:
        output = subprocess.check_output(["sensors"], text=True)

        # Match lines containing "GPU" or other likely labels
        fan_speeds = re.findall(r"(.+?):\s+(\d+)\s*RPM", output)

        for label, speed in fan_speeds:
            if "gpu" in label.lower() or "fan2" in label.lower():  # Common labels for GPU fans
                return int(speed)

        # If GPU label isn't found, return the second available fan speed as fallback
        return int(fan_speeds[1][1]) if len(fan_speeds) > 1 else None
    except Exception:
        return None