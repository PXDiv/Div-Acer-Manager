using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;
using Avalonia.Controls;

namespace DAFC_GUI
{
    public class ConfigManager
    {
        private const string ConfigPath = "/var/lib/acer_fan_control/config.json";
        
        // Configuration model class
        public class ConfigSettings
        {
            public int min_speed { get; set; } = 640;
            public int max_speed { get; set; } = 2560;
            public bool dynamic_mode { get; set; } = true;
            public List<TempStep> temp_steps { get; set; } = new List<TempStep>
            {
                new TempStep { temperature = 50, speed = 1024 },
                new TempStep { temperature = 70, speed = 1536 },
                new TempStep { temperature = 80, speed = 2048 },
                new TempStep { temperature = 85, speed = 2176 },  // Added default value
                new TempStep { temperature = 90, speed = 2304 },  // Added default value
                new TempStep { temperature = 95, speed = 2432 }   // Added default value
            };
        }

        public class TempStep
        {
            public int temperature { get; set; }
            public int speed { get; set; }
        }

        // Load config from file
        public ConfigSettings LoadConfig(bool forceRefresh = false)
        {
            try
            {
                if (File.Exists(ConfigPath))
                {
                    // Use FileOptions.None for no caching
                    using (FileStream fs = new FileStream(ConfigPath, FileMode.Open, FileAccess.Read, FileShare.Read, 4096, FileOptions.None))
                    using (StreamReader reader = new StreamReader(fs))
                    {
                        string jsonContent = reader.ReadToEnd();
                        var config = JsonSerializer.Deserialize<ConfigSettings>(jsonContent);
                        
                        // Ensure we have 6 temperature steps
                        if (config != null)
                        {
                            EnsureTemperatureSteps(config);
                            return config;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to load configuration: {ex.Message}");
            }
    
            var defaultConfig = new ConfigSettings();
            EnsureTemperatureSteps(defaultConfig);
            return defaultConfig;
        }

        // Ensure config has 6 temperature steps
        private void EnsureTemperatureSteps(ConfigSettings config)
        {
            // Make sure we have at least 6 temperature steps
            if (config.temp_steps == null)
            {
                config.temp_steps = new List<TempStep>();
            }
            
            // Add default temperature steps if needed
            while (config.temp_steps.Count < 6)
            {
                int index = config.temp_steps.Count;
                int temp = 50 + (index * 10);
                int speed = config.min_speed + ((index + 1) * (config.max_speed - config.min_speed) / 7);
                
                config.temp_steps.Add(new TempStep { temperature = temp, speed = speed });
            }
        }

        // Save config to file
        public void SaveConfig(ConfigSettings config)
        {
            try
            {
                // Ensure directory exists
                Directory.CreateDirectory(Path.GetDirectoryName(ConfigPath));
                
                // Ensure we have all required temperature steps
                EnsureTemperatureSteps(config);
                
                string jsonContent = JsonSerializer.Serialize(config, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(ConfigPath, jsonContent);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to save configuration: {ex.Message}");
            }
        }

        // Update UI with loaded settings
        public void UpdateUI(Window window, ConfigSettings config)
        {
            // Make sure we have all required temperature steps
            EnsureTemperatureSteps(config);
            
            // Get controls from the window
            var cpuFanSlider = window.FindControl<Slider>("CpuFanSlider");
            var gpuFanSlider = window.FindControl<Slider>("GpuFanSlider");
            var mixedFanSlider = window.FindControl<Slider>("AllFanSlider");
            var dynamicCheckBox = window.FindControl<CheckBox>("DynamicFanControlCheckBox");
            
            if (cpuFanSlider != null)
            {
                cpuFanSlider.Minimum = config.min_speed;
                cpuFanSlider.Maximum = config.max_speed;
            }
            
            if (gpuFanSlider != null)
            {
                gpuFanSlider.Minimum = config.min_speed;
                gpuFanSlider.Maximum = config.max_speed;
            }
            
            if (mixedFanSlider != null)
            {
                mixedFanSlider.Minimum = config.min_speed;
                mixedFanSlider.Maximum = config.max_speed;
            }
            
            if (dynamicCheckBox != null)
            {
                dynamicCheckBox.IsChecked = config.dynamic_mode;
            }
            

            
            // Update temperature step controls if they exist
            UpdateTempStepUI(window, "T1TempInput", "T1Slider", config.temp_steps[0], config);
            UpdateTempStepUI(window, "T2TempInput", "T2Slider", config.temp_steps[1], config);
            UpdateTempStepUI(window, "T3TempInput", "T3Slider", config.temp_steps[2], config);
            UpdateTempStepUI(window, "T4TempInput", "T4Slider", config.temp_steps[3], config);
            UpdateTempStepUI(window, "T5TempInput", "T5Slider", config.temp_steps[4], config);
            UpdateTempStepUI(window, "T6TempInput", "T6Slider", config.temp_steps[5], config);
        }
        
        private void UpdateTempStepUI(Window window, string tempControlName, string speedControlName, TempStep step, ConfigSettings config)
        {
            var tempControl = window.FindControl<NumericUpDown>(tempControlName);
            var speedControl = window.FindControl<Slider>(speedControlName);
            
            if (tempControl != null)
                tempControl.Text = step.temperature.ToString();
                
            if (speedControl != null)
            {
                speedControl.Value = (int)step.speed;
                speedControl.Minimum = config.min_speed;
                speedControl.Maximum = config.max_speed;
            }
        }
        
        // Create config from UI
        public ConfigSettings CreateConfigFromUI(Window window)
        {
            var cpuFanSlider = window.FindControl<Slider>("CpuFanSlider");
            var gpuFanSlider = window.FindControl<Slider>("GpuFanSlider");
            var dynamicCheckBox = window.FindControl<CheckBox>("DynamicFanControlCheckBox");
            
            var config = new ConfigSettings
            {
                min_speed = (int)(cpuFanSlider?.Minimum ?? 640),
                max_speed = (int)(cpuFanSlider?.Maximum ?? 2560),
                dynamic_mode = dynamicCheckBox?.IsChecked ?? true,
                temp_steps = new List<TempStep>()
            };
            
            // Get temperature steps from UI
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp1TextBox", "Speed1TextBox", 50, 1024));
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp2TextBox", "Speed2TextBox", 70, 1536));
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp3TextBox", "Speed3TextBox", 80, 2048));
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp4TextBox", "Speed4TextBox", 85, 2176));
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp5TextBox", "Speed5TextBox", 90, 2304));
            config.temp_steps.Add(GetTempStepFromUI(window, "Temp6TextBox", "Speed6TextBox", 95, 2432));
            
            return config;
        }
        
        private TempStep GetTempStepFromUI(Window window, string tempControlName, string speedControlName, int defaultTemp, int defaultSpeed)
        {
            var tempControl = window.FindControl<TextBox>(tempControlName);
            var speedControl = window.FindControl<TextBox>(speedControlName);
            
            int temp = defaultTemp;
            int speed = defaultSpeed;
            
            if (tempControl != null && int.TryParse(tempControl.Text, out int parsedTemp))
                temp = parsedTemp;
                
            if (speedControl != null && int.TryParse(speedControl.Text, out int parsedSpeed))
                speed = parsedSpeed;
                
            return new TempStep { temperature = temp, speed = speed };
        }
    }
}