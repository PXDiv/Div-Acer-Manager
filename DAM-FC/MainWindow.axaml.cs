//DAMFC-GUI v 1.20

using Avalonia.Controls;
using Avalonia.Interactivity;
using System;
using System.Diagnostics;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Avalonia.Controls.Primitives;

namespace DAFC_GUI;

public partial class MainWindow : Window
{
    private static readonly string GuiVersion = "1.20";
    
    private readonly ConfigManager _configManager = new ConfigManager();
    public ConfigManager.ConfigSettings CurrentConfig;
    public MainWindow()
    {
        InitializeComponent();
        VersionText.Text = "GUI version: " +
                           "v" + GuiVersion;
    }

    private const string SocketPath = "/var/run/fan_control_daemon.sock";
    private const string ConfigPath = "/var/lib/acer_fan_control/config.json";

    // Call this when your window is loaded
    protected override void OnOpened(EventArgs e)
    {
        base.OnOpened(e);
            
        // Load configuration and update UI
        CurrentConfig = _configManager.LoadConfig();
        _configManager.UpdateUI(this, CurrentConfig);
    }
    
    public void UpdateConfigAndReloadUi()
    {
        UpdateConfig();
        Console.WriteLine("Updated config");
        
        System.Threading.Thread.Sleep(100); // 100ms delay to ensure the file gets saved properly (without this, it causes bugs)
        
        CurrentConfig = _configManager.LoadConfig(true);
        Console.WriteLine(CurrentConfig.min_speed);
        
        _configManager.UpdateUI(this, _configManager.LoadConfig());
        Console.WriteLine("Updated UI Based on Current Config");
        
    }

    
    public void SaveSettingsButton_OnClick(object sender, RoutedEventArgs e)
    {
        UpdateConfigAndReloadUi();
    }
    
    public void SetFanSpeed(int fanNumber, int speed)
    {
        var command = new 
        {
            type = "set_fan_speed",
            fan = fanNumber,
            speed = speed
        };

        SendCommand(command);
    }

    public void SetDynamicMode(bool dynamicMode)
    {
        var command = new
        {
            type = "set_dynamic_mode",
            toActivate = dynamicMode
        };
        
        SendCommand(command);
    }

    public void CompileFanDrivers()
    {
        var command = new
        {
            type = "compile_drivers",
        };
    
        SendCommand(command);
    }
    
    public void LoadFanDrivers()
    {
        var command = new
        {
            type = "load_drivers",
        };
    
        SendCommand(command);
    }
    
    public void UnloadFanDrivers()
    {
        var command = new
        {
            type = "unload_drivers",
        };
    
        SendCommand(command);
    }


    public void CleanFanDrivers()
    {
        var command = new
        {
            type = "clean_compiled_drivers",
        };
    
        SendCommand(command);
    }
    
    public void ReloadCompileFanDrivers()
    {
        var command = new
        {
            type = "reload_complied_drivers",
        };
    
        SendCommand(command);
    } 

    void SendCommandString(string commandString)
    {
        var command = new
        {
            type = commandString,
        };
    
        SendCommand(command);
    }
    
    public void UpdateConfig()
    {
        var config = new
        {
            min_speed = (int)MinSpeedInput.Value,
            max_speed = (int)MaxSpeedInput.Value,
            dynamic_mode = DynamicFanControlCheckBox.IsChecked.Value,
            temp_steps = new[]
            {
                new { temperature = Convert.ToInt32(T1TempInput.Text), speed = Convert.ToInt32(T1Slider.Value) },
                new { temperature = Convert.ToInt32(T2TempInput.Text), speed = Convert.ToInt32(T2Slider.Value) },
                new { temperature = Convert.ToInt32(T3TempInput.Text), speed = Convert.ToInt32(T3Slider.Value) },
                new { temperature = Convert.ToInt32(T4TempInput.Text), speed = Convert.ToInt32(T4Slider.Value) },
                new { temperature = Convert.ToInt32(T5TempInput.Text), speed = Convert.ToInt32(T5Slider.Value) },
                new { temperature = Convert.ToInt32(T6TempInput.Text), speed = Convert.ToInt32(T6Slider.Value) }
            }
        };

        var command = new
        {
            type = "update_config",
            config = config 
        };
    
        SendCommand(command);
    }

    private void SendCommand(object command)
    {
        try
        {
            using (var client = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified))
            {
                var endpoint = new UnixEndPoint(SocketPath);
            
                try
                {
                    client.Connect(endpoint);
                
                    var jsonCommand = JsonSerializer.Serialize(command);
                    var buffer = Encoding.UTF8.GetBytes(jsonCommand);
                
                    client.Send(buffer);
                }
                catch (SocketException ex)
                {
                    ShowMessageDialog("Connection Error", 
                        $"Could not connect to fan control daemon: {ex.Message}\n\nPlease make sure the daemon is running.");
                }
            }
        }
        catch (Exception ex)
        {
            ShowMessageDialog("Error", $"An error occurred: {ex.Message}");
        }
    }

    private void ShowMessageDialog(string title, string message)
    {
        // Create and show a message box for various Messages
        var messageBox = new Window
        {
            Title = title,
            Width = 400,
            Height = 150,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            Content = new StackPanel
            {
                Margin = new Avalonia.Thickness(20),
                Children =
                {
                    new TextBlock
                    {
                        Text = message,
                        TextWrapping = Avalonia.Media.TextWrapping.Wrap,
                        Margin = new Avalonia.Thickness(0, 0, 0, 20)
                    },
                    new Button
                    {
                        Content = "OK",
                        HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center
                    }
                }
            }
        };
    
        // Add click handler for the OK button
        var okButton = ((StackPanel)messageBox.Content).Children[1] as Button;
        if (okButton != null)
        {
            okButton.Click += (sender, args) => messageBox.Close();
        }
    
        messageBox.ShowDialog(this);
    }

    public void ManualSettingApplyButton_OnClick(object? sender, RoutedEventArgs e)
    {
        DynamicFanControlCheckBox.IsChecked = false;
        UpdateConfig();
        SetFanSpeed(1, (int)CpuFanSlider.Value);
        SetFanSpeed(2, (int)GpuFanSlider.Value);
        DisableDynamicMode();
    }

    private void DisableDynamicMode()
    {
        SetDynamicMode(false);
        DynamicFanControlCheckBox.IsChecked = false;
    }

    private void DynamicFanControlCheckBox_OnClick(object? sender, RoutedEventArgs e)
    {
        SetDynamicMode(DynamicFanControlCheckBox.IsChecked != null && DynamicFanControlCheckBox.IsChecked.Value);
        UpdateConfig();
    }

    private void AllFanSlider_OnValueChanged(object? sender, RangeBaseValueChangedEventArgs e)
    {
        CpuFanSlider.Value = GpuFanSlider.Value = AllFanSlider.Value;
    }

    private void MaxSpeedButton_OnClick(object? sender, RoutedEventArgs e)
    {
        SetFanSpeed(1, CurrentConfig.max_speed);
        SetFanSpeed(2, CurrentConfig.max_speed);
        DisableDynamicMode();
    }
    
    private void QuickStepButton_OnClick(object? sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.CommandParameter is double param)
        {
            Console.WriteLine(param);
            SetFanSpeed(1, Convert.ToInt16( param));
            SetFanSpeed(2, Convert.ToInt16( param));
            DisableDynamicMode();
        }
    }

    private void Clean_Drivers_Button_OnClick(object? sender, RoutedEventArgs e)
    {
        CleanFanDrivers();
        UnloadFanDrivers();
    }

    private void ReloadCompiledDriversButton_OnClick(object? sender, RoutedEventArgs e)
    {
       ReloadCompileFanDrivers();
    }

    private void CompileAndLoadDriversButton_OnClick(object? sender, RoutedEventArgs e)
    {
        CompileFanDrivers();
        LoadFanDrivers();
    }

    private void ExitButton_OnClick(object? sender, RoutedEventArgs e)
    {
        this.Close();
    }

    private void UpdatesButton_OnClick(object? sender, RoutedEventArgs e)
    {
        var url = "https://github.com/PXDiv/Div-Acer-Manager/releases";
        Process.Start("xdg-open", url);
    }

    private void HealthModeCheckBox_OnClick(object? sender, RoutedEventArgs e)
    {
        
    }
}