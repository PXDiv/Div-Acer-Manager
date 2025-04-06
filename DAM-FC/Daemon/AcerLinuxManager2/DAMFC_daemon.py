# DAMFC_Daemon v0.8.2 

import os
import json
import time
import logging
import threading
import socket
import json
import signal
import sys
from DriverManager import DriverManager
import HardwareStatus

class FanControlDaemon:
    def __init__(self, config_path='/var/lib/acer_fan_control/config.json'):
        # Setup logging with more detailed output
        self.setup_logging()
        
        logging.info("Initializing Fan Control Daemon")
        logging.info(f"Config path: {config_path}")
        
        self.config_path = config_path
        self.config = self.load_config()
        self.running = False
        
        # Initialize dynamic mode from config
        self.dynamicModeEnabled = self.config.get('dynamic_mode', True)
        logging.info(f"Dynamic mode initialized to: {self.dynamicModeEnabled}")
    
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def setup_logging(self):
        # Ensure log directory exists
        log_dir = '/var/log/acer_fan_control'
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging with more detailed format
        logging.basicConfig(
            filename=os.path.join(log_dir, 'fan_control_daemon.log'), 
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler for additional visibility
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(console_handler)
        
        logging.info("Logging system initialized")

    def load_config(self):
        logging.info(f"Attempting to load configuration from {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logging.info("Configuration loaded successfully")
                return config
        except FileNotFoundError:
            logging.warning("No configuration file found. Using default settings.")
            return {
                'min_speed': 640,
                'max_speed': 2560,
                'dynamic_mode': True,
                'temp_steps': [
                    {'temperature': 50, 'speed': 1024},
                    {'temperature': 70, 'speed': 1536},
                    {'temperature': 80, 'speed': 2048}
                ]
            }
        except json.JSONDecodeError:
            logging.error("Error decoding configuration file. Using default settings.")
            return {
                'min_speed': 640,
                'max_speed': 2560,
                'dynamic_mode': True,
                'temp_steps': [
                    {'temperature': 50, 'speed': 1024},
                    {'temperature': 70, 'speed': 1536},
                    {'temperature': 80, 'speed': 2048}
                ]
            }

    def save_config(self):
        logging.info("Saving current configuration")
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")

    def get_cpu_temp(self):
        try:
            return int(HardwareStatus.get_cpu_temp())
            
        except Exception as e:
            logging.error(f"Error reading CPU temperature: {e}")
            return 0

    def get_gpu_temp(self):
        try:
            temp = HardwareStatus.get_gpu_temp()
            if isinstance(temp, str):  # Check if it's a string (like "N/A")
                return 0  # Return a safe default value
            return int(temp)
        except Exception as e:
            logging.error(f"Could not read GPU temperature: {e}")
            return 0 

    def set_fan_speed(self, fan_number, speed):
        try:
            if 0 < int(fan_number) < 3:
                fan_file = f'/dev/fan{fan_number}'
                # logging.info(f"Attempting to set Fan {fan_number} speed to {speed}")
                
                # Validate speed is within acceptable range
                if speed < self.config.get('min_speed', 640):
                    speed = self.config.get('min_speed', 640)
                    logging.warning(f"Speed adjusted to minimum: {speed}")
                
                if speed > self.config.get('max_speed', 2560):
                    speed = self.config.get('max_speed', 2560)
                    logging.warning(f"Speed adjusted to maximum: {speed}")
                
                with open(fan_file, 'w') as f:
                    os.system(f"sudo echo {speed} | tee /dev/fan{fan_number}")
                logging.info(f"Successfully set Fan {fan_number} to speed {speed}")
            else:
                logging.error(f"Invalid fan number: {fan_number}")
        except PermissionError:
            logging.error(f"Permission denied when setting fan {fan_number} speed. Run with sudo?")
        except FileNotFoundError:
            logging.error(f"Fan control file not found: /dev/fan{fan_number}")
        except Exception as e:
            logging.error(f"Could not set fan speed: {e}")

    def dynamic_fan_control(self):

        logging.info("Starting dynamic fan control thread")
        while self.running:
            if self.dynamicModeEnabled == True:
                # try:
                cpu_temp = self.get_cpu_temp()
                gpu_temp = self.get_gpu_temp()

                logging.debug(f"Current temperatures - CPU: {cpu_temp}°C, GPU: {gpu_temp}°C")

                # Dynamic fan speed logic
                max_temp = max(cpu_temp, gpu_temp)
                
                for step in sorted(self.config.get('temp_steps', []), key=lambda x: x['temperature'], reverse=True):
                    if max_temp >= step['temperature']:
                        logging.info(f"Setting fans to {step['speed']} due to temperature {max_temp}°C")
                        self.set_fan_speed(1, step['speed'])  # CPU Fan
                        self.set_fan_speed(2, step['speed'])  # GPU Fan
                        break

                # except Exception as e:
                #     logging.error(f"Error in dynamic fan control: {e}")

                time.sleep(5)  # Check every 5 seconds
        
        logging.info("Dynamic fan control thread stopped")

    def start(self):
        logging.info("Starting Fan Control Daemon")
        self.running = True
        
        # Start dynamic fan control in a separate thread
        fan_thread = threading.Thread(target=self.dynamic_fan_control)
        fan_thread.daemon = True  # Allow thread to be killed when main process exits
        fan_thread.start()
        
        logging.info("Daemon started successfully")

    def shutdown(self, signum=None, frame=None):
        logging.info(f"Received shutdown signal {signum}. Stopping daemon.")
        self.running = False
        # Additional cleanup can be added here
        sys.exit(0)

    def handle_socket_commands(self):
        # Unix domain socket for IPC with C# GUI
        socket_path = '/var/run/fan_control_daemon.sock'

        logging.info(f"Preparing Unix socket at {socket_path}")

        if os.path.exists(socket_path):
            os.unlink(socket_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(socket_path)

        # Set socket permissions to allow non-root access if needed
        os.chmod(socket_path, 0o666)

        sock.listen(1)
        logging.info("Socket listening for connections")

        while self.running:
            try:
                connection, client_address = sock.accept()
                logging.info(f"Connection from {client_address}")

                try:
                    data = connection.recv(1024)
                    if data:
                        command = json.loads(data.decode())
                        # logging.info(f"Received command: {command}")
                        response = self.process_command(command)

                        # Send response back if there is one
                        if response:
                            connection.sendall(json.dumps(response).encode())
                except json.JSONDecodeError:
                    logging.error("Invalid JSON received")
                except Exception as e:
                    logging.error(f"Error processing socket command: {e}")
                finally:
                    connection.close()
            except Exception as e:
                logging.error(f"Socket connection error: {e}")
                time.sleep(1)  # Prevent tight error loop
    
    def process_command(self, command):
        logging.info(f"Processing command: {command}")
        
        try:
            if command['type'] == 'set_fan_speed':
                self.set_fan_speed(command['fan'], command['speed'])

            elif command['type'] == 'update_config':
                logging.info("Updating configuration")
                self.config = command['config']
                self.save_config()

            elif command['type'] == 'get_temp':
                return {
                    'cpu_temp': self.get_cpu_temp(),
                    'gpu_temp': self.get_gpu_temp()
                }
            
            elif command['type'] == 'set_dynamic_mode':
                self.dynamicModeEnabled = command['toActivate']
                logging.info(f"Dynamic mode set to: {self.dynamicModeEnabled}")
                   
            elif command['type'] == 'get_driver_status':
                return DriverManager.get_driver_status()
            
            elif command['type'] == 'clean_compiled_drivers':
                DriverManager.clean_compiled_drivers()
            
            elif command['type'] == 'reload_complied_drivers':
                DriverManager.remove_driver()
                DriverManager.remove_fan_control_files()
                DriverManager.ensure_driver_loaded()

            elif command['type'] == 'unload_drivers':
                DriverManager.remove_driver()
            
            elif command['type'] == 'compile_drivers':
                DriverManager.compile_driver()
                
            elif command['type'] == 'load_drivers':
                DriverManager.load_driver()
            
            else:
                logging.warning(f"Unknown command type: {command['type']}")
        except KeyError as e:
            logging.error(f"Missing key in command: {e}")
        except Exception as e:
            logging.error(f"Error processing command: {e}")

def main():
    daemon = FanControlDaemon()
    DriverManager.remove_fan_control_files()
    DriverManager.ensure_driver_loaded()
    daemon.start()
    daemon.handle_socket_commands()

if __name__ == '__main__':
    main()