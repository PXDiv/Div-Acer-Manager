# DAMFC_DriverManager v0.3.0
# With Battery Functions to be implemented later in daemon

import os
import subprocess
import logging

class DriverManager:
    # Use absolute paths to prevent working directory issues
    # Assuming your drivers are in a directory relative to the script
    DRIVER_DIR = "NitroDrivers"
    MODULE_NAME = "acer_nitro_gaming_driver2.ko"
    MODULE_PATH = os.path.join(DRIVER_DIR, MODULE_NAME)
    
    # Battery control paths
    BATTERY_MODULE_NAME = "acer-wmi-battery"
    BATTERY_SYSFS_PATH = "/sys/bus/wmi/drivers/acer-wmi-battery"
    BATTERY_HEALTH_PATH = os.path.join(BATTERY_SYSFS_PATH, "health_mode")
    BATTERY_CALIBRATION_PATH = os.path.join(BATTERY_SYSFS_PATH, "calibration_mode")
    BATTERY_TEMPERATURE_PATH = os.path.join(BATTERY_SYSFS_PATH, "temperature")
    
    @staticmethod
    def is_driver_loaded():
        """Check if the module is currently loaded."""
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            module_name = DriverManager.MODULE_NAME.split(".")[0]
            is_loaded = module_name in result.stdout
            logging.info(f"Driver status check: {module_name} is {'loaded' if is_loaded else 'not loaded'}")
            return is_loaded
        except Exception as e:
            logging.error(f"Error checking if driver is loaded: {e}")
            return False
    
    @staticmethod
    def remove_driver():
        """Remove the module if it is loaded."""
        try:
            module_name = DriverManager.MODULE_NAME.split(".")[0]
            logging.info(f"Attempting to remove driver: {module_name}")
            
            result = subprocess.run(["sudo", "rmmod", module_name], capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Driver removed successfully")
                return True
            else:
                logging.error(f"Failed to remove driver: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error during driver removal: {e}")
            return False
    
    @staticmethod
    def remove_fan_control_files():
        """Remove fan control device files if they exist."""
        try:
            success = True
            for fan in ["/dev/fan1", "/dev/fan2"]:
                if os.path.exists(fan):
                    logging.info(f"Removing fan control file: {fan}")
                    result = subprocess.run(["sudo", "rm", "-f", fan], capture_output=True, text=True)
                    if result.returncode != 0:
                        logging.error(f"Failed to remove {fan}: {result.stderr}")
                        success = False
            return success
        except Exception as e:
            logging.error(f"Error removing fan control files: {e}")
            return False
    
    @staticmethod
    def compile_driver():
        """Compile the driver if not already compiled."""
        try:
            logging.info(f"Checking for driver at: {DriverManager.MODULE_PATH}")
            logging.info(f"Driver directory: {DriverManager.DRIVER_DIR}")
            
            if not os.path.exists(DriverManager.DRIVER_DIR):
                logging.error(f"Driver directory not found: {DriverManager.DRIVER_DIR}")
                return False
                
            if not os.path.exists(DriverManager.MODULE_PATH):
                logging.info("Driver not compiled. Running make...")
                
                process = subprocess.run("make", cwd=DriverManager.DRIVER_DIR, shell=True, 
                                         capture_output=True, text=True)
                
                if process.returncode != 0:
                    logging.error(f"Make failed: {process.stderr}")
                    return False
                
                if process.stderr:
                    logging.warning(f"Make warnings: {process.stderr}")
                
                if not os.path.exists(DriverManager.MODULE_PATH):
                    logging.error(f"Driver file not found after compilation: {DriverManager.MODULE_PATH}")
                    return False
                
                logging.info("Driver compiled successfully")
                return True
            else:
                logging.info("Using existing compiled driver")
                return True
        except Exception as e:
            logging.error(f"Error during driver compilation: {e}")
            return False
    
    @staticmethod
    def clean_compiled_drivers():
        """Clean compiled driver files."""
        try:
            if os.path.exists(DriverManager.DRIVER_DIR):
                logging.info("Running make clean...")
                
                process = subprocess.run("make clean", cwd=DriverManager.DRIVER_DIR, shell=True, 
                                         capture_output=True, text=True)
                
                if process.returncode != 0:
                    logging.error(f"Make clean failed: {process.stderr}")
                    return False
                
                logging.info("Compiled drivers have been cleaned")
                return True
            else:
                logging.warning(f"Driver directory not found: {DriverManager.DRIVER_DIR}")
                return False
        except Exception as e:
            logging.error(f"Error during make clean: {e}")
            return False
    
    @staticmethod
    def load_driver():
        """Load the compiled driver."""
        try:
            if not os.path.exists(DriverManager.MODULE_PATH):
                logging.error(f"Driver file not found: {DriverManager.MODULE_PATH}")
                return False
            
            logging.info(f"Loading driver: {DriverManager.MODULE_PATH}")
            
            result = subprocess.run(["sudo", "insmod", os.path.abspath(DriverManager.MODULE_PATH)], 
                                    capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Driver loaded successfully")
                return True
            else:
                logging.error(f"Failed to load driver: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error loading driver: {e}")
            return False
    
    @staticmethod
    def get_driver_status():
        """Return a dict with driver status information."""
        return {
            "is_loaded": DriverManager.is_driver_loaded(),
            "driver_path": os.path.abspath(DriverManager.MODULE_PATH) if os.path.exists(DriverManager.MODULE_PATH) else None,
            "driver_directory_exists": os.path.exists(DriverManager.DRIVER_DIR),
            "device_files": {
                "fan1": os.path.exists("/dev/fan1"),
                "fan2": os.path.exists("/dev/fan2")
            },
            "battery_driver": {
                "is_loaded": DriverManager.is_battery_driver_loaded(),
                "health_mode": DriverManager.get_battery_health_mode(),
                "calibration_mode": DriverManager.get_battery_calibration_mode(),
                "temperature": DriverManager.get_battery_temperature(),
            }
        }
    
    @staticmethod
    def set_driver_path(driver_dir=None):
        """Manually set the driver directory path"""
        if driver_dir and os.path.exists(driver_dir):
            DriverManager.DRIVER_DIR = driver_dir
            DriverManager.MODULE_PATH = os.path.join(driver_dir, DriverManager.MODULE_NAME)
            logging.info(f"Driver path set to: {DriverManager.DRIVER_DIR}")
            return True
        return False
    
    @staticmethod
    def ensure_driver_loaded():
        """Make sure the driver is loaded, loading it if necessary."""
        if DriverManager.is_driver_loaded():
            logging.info("Driver is already loaded")
            return True
        
        if not os.path.exists(DriverManager.DRIVER_DIR):
            logging.error(f"Driver directory not found: {DriverManager.DRIVER_DIR}")
            return False
            
        if not os.path.exists(DriverManager.MODULE_PATH) and not DriverManager.compile_driver():
            logging.error("Failed to compile driver")
            return False
        
        return DriverManager.load_driver()
    
    # Battery driver management methods
    @staticmethod
    def is_battery_driver_loaded():
        """Check if the Acer WMI battery driver is loaded."""
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            is_loaded = DriverManager.BATTERY_MODULE_NAME in result.stdout
            logging.info(f"Battery driver status check: {DriverManager.BATTERY_MODULE_NAME} is {'loaded' if is_loaded else 'not loaded'}")
            return is_loaded
        except Exception as e:
            logging.error(f"Error checking if battery driver is loaded: {e}")
            return False
    
    @staticmethod
    def load_battery_driver():
        """Load the Acer WMI battery driver."""
        try:
            logging.info(f"Loading Acer WMI battery driver: {DriverManager.BATTERY_MODULE_NAME}")
            result = subprocess.run(["sudo", "modprobe", DriverManager.BATTERY_MODULE_NAME], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Battery driver loaded successfully")
                return True
            else:
                logging.error(f"Failed to load battery driver: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error loading battery driver: {e}")
            return False
    
    @staticmethod
    def unload_battery_driver():
        """Unload the Acer WMI battery driver."""
        try:
            logging.info(f"Unloading Acer WMI battery driver: {DriverManager.BATTERY_MODULE_NAME}")
            result = subprocess.run(["sudo", "rmmod", DriverManager.BATTERY_MODULE_NAME], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Battery driver unloaded successfully")
                return True
            else:
                logging.error(f"Failed to unload battery driver: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error unloading battery driver: {e}")
            return False
    
    @staticmethod
    def ensure_battery_driver_loaded():
        """Make sure the battery driver is loaded, loading it if necessary."""
        if DriverManager.is_battery_driver_loaded():
            logging.info("Battery driver is already loaded")
            return True
        else:
            return DriverManager.load_battery_driver()
    
    @staticmethod
    def get_battery_health_mode():
        """Get the current battery health mode state."""
        try:
            if not DriverManager.is_battery_driver_loaded():
                return -1  # Driver not loaded
                
            with open(DriverManager.BATTERY_HEALTH_PATH, 'r') as f:
                value = int(f.read().strip())
                return value
        except FileNotFoundError:
            logging.error("Battery health mode file not found")
            return -1
        except Exception as e:
            logging.error(f"Error reading battery health mode: {e}")
            return -1
    
    @staticmethod
    def set_battery_health_mode(enabled):
        """Set the battery health mode."""
        try:
            if not DriverManager.is_battery_driver_loaded():
                logging.error("Cannot set health mode: Battery driver not loaded")
                return False
                
            value = 1 if enabled else 0
            with open(DriverManager.BATTERY_HEALTH_PATH, 'w') as f:
                f.write(str(value))
            logging.info(f"Battery health mode set to: {enabled}")
            return True
        except FileNotFoundError:
            logging.error("Battery health mode file not found")
            return False
        except Exception as e:
            logging.error(f"Error setting battery health mode: {e}")
            return False
    
    @staticmethod
    def get_battery_calibration_mode():
        """Get the current battery calibration mode state."""
        try:
            if not DriverManager.is_battery_driver_loaded():
                return -1  # Driver not loaded
                
            with open(DriverManager.BATTERY_CALIBRATION_PATH, 'r') as f:
                value = int(f.read().strip())
                return value
        except FileNotFoundError:
            logging.error("Battery calibration mode file not found")
            return -1
        except Exception as e:
            logging.error(f"Error reading battery calibration mode: {e}")
            return -1
    
    @staticmethod
    def set_battery_calibration_mode(enabled):
        """Set the battery calibration mode."""
        try:
            if not DriverManager.is_battery_driver_loaded():
                logging.error("Cannot set calibration mode: Battery driver not loaded")
                return False
                
            value = 1 if enabled else 0
            with open(DriverManager.BATTERY_CALIBRATION_PATH, 'w') as f:
                f.write(str(value))
            logging.info(f"Battery calibration mode set to: {enabled}")
            return True
        except FileNotFoundError:
            logging.error("Battery calibration mode file not found")
            return False
        except Exception as e:
            logging.error(f"Error setting battery calibration mode: {e}")
            return False
    
    @staticmethod
    def get_battery_temperature():
        """Get the current battery temperature."""
        try:
            if not DriverManager.is_battery_driver_loaded():
                return -1  # Driver not loaded
                
            with open(DriverManager.BATTERY_TEMPERATURE_PATH, 'r') as f:
                # Temperature is in 0.1 degrees Celsius
                value = int(f.read().strip()) / 100.0
                return value
        except FileNotFoundError:
            logging.error("Battery temperature file not found")
            return -1
        except Exception as e:
            logging.error(f"Error reading battery temperature: {e}")
            return -1
    
    @staticmethod
    def apply_battery_settings(health_mode=None, calibration_mode=None):
        """Apply battery settings if battery driver is loaded."""
        if not DriverManager.is_battery_driver_loaded():
            logging.warning("Cannot apply battery settings: Driver not loaded")
            return False
        
        success = True
        
        # Apply health mode if specified
        if health_mode is not None:
            if not DriverManager.set_battery_health_mode(health_mode):
                success = False
        
        # Apply calibration mode if specified
        if calibration_mode is not None:
            if not DriverManager.set_battery_calibration_mode(calibration_mode):
                success = False
        
        return success
