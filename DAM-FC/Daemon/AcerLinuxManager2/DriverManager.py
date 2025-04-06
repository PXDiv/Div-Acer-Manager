# DAMFC_DriverManager v0.2.3
import os
import subprocess
import logging

class DriverManager:
    # Use absolute paths to prevent working directory issues
    # Assuming your drivers are in a directory relative to the script
    DRIVER_DIR = "NitroDrivers"
    MODULE_NAME = "acer_nitro_gaming_driver2.ko"
    MODULE_PATH = os.path.join(DRIVER_DIR, MODULE_NAME)
    
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