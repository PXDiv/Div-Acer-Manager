<h1>
  <img src="https://github.com/user-attachments/assets/3b24a278-6c55-461c-9a15-0ca465c26479" alt="fan-control-icon" height="60" style="vertical-align: middle; margin-right: 8px;">
  DAM Fan Controls for Acer Nitro & Predator (Linux)
</h1>

Fan control and thermal management suite for Acer Nitro &amp; Predator laptops on Linux. Features secure WMI-based driver, intelligent background daemon, and a modern Avalonia-based GUI.

**DAM Fan Controls** is a powerful thermal management tool for newer **Acer Nitro** and **Predator** laptops running Linux.  
It uses the WMI interface to provide **dynamic fan control**, backed by a secure kernel driver, a smart background **daemon**, and a modern **GUI written in C# using Avalonia UI**.

![Screenshot From 2025-04-06 20-17-46](https://github.com/user-attachments/assets/df9e2121-2254-415f-ad17-1b09a06d83b7)

---

## 🔄 What’s New?

This project is a complete rewrite and continuation of the earlier **AcerLinuxManager**.  
While the original worked, it had several limitations:

❌ Barebones and clunky GUI  
❌ No background daemon – had to keep GUI running constantly  
❌ GUI required root privileges  
❌ No proper installation or service setup  

The new version fixes all of that with:

✅ A fully redesigned GUI using **C# and Avalonia**  
✅ A Better Backend Driver, with Better Security
✅ A python **daemon** that runs independently in the background  
✅ Clean **SystemD integration** – daemon starts at boot, no password needed  
✅ No need to keep the GUI running  
✅ Much better **security, performance, and stability**

---

## 🧰 Features

- ✅ Manual & automatic **fan speed control**
- ✅ Smart **dynamic fan control** based on system temperature
- ✅ Modern and fast GUI using **Avalonia UI**
- ✅ Clean background **daemon** with inter-process communication
- ✅ Auto-compile & load drivers on install
- ✅ Auto-load drivers on boot via system service
- ✅ Save and restore settings easily
- ✅ Simple **log-based troubleshooting** (`/var/log/acer_fan_control/`)
- ✅ Clean driver unload & cleanup options

---

## 🧪 Compatibility

This driver only works on **Acer laptops that use the WMI interface** for fan control.  
Most **Nitro** and **Predator** models from recent years are supported.

---

## 📦 Installation

1. Download the **latest release** from the [Releases](#) section.  
2. Extract the archive.
3. Run the setup script:
   ```bash
   ./SetupDrivers.sh
   ```
4. Choose option `1` for installation.
5. Reboot your system.

After reboot, the daemon should auto-start, and your fan control should be ready.

---

## ⚙️ First-Time Configuration

1. Open **DAM Fan Controls** from your application launcher.
2. Go to the **Advanced** tab.
3. Set the **Fan Speed Range** depending on your laptop model:
   - Some models use `512 - 2560`
   - Others use `128 - 512`
4. Always use values that are **multiples of 128**.
5. Click **Apply Changes**.
6. Then **Compile & Load Drivers** using the GUI button.

---

## 🛠️ Troubleshooting

If things aren't working as expected:

### 1. Driver Compilation Fails
Make sure you’ve installed the correct **kernel headers** for your current Linux kernel:

```bash
# For Ubuntu/Debian-based systems
sudo apt install linux-headers-$(uname -r)
```

Then reboot and try **compiling/loading drivers again** from the GUI.

### 2. Manual Compilation
Navigate to:
```bash
cd /opt/dam-fan-controls/NitroDrivers
sudo make
```

Check for any errors and search online if necessary. You can also check logs at:
```bash
/var/log/acer_fan_control/
```

---

## ❤️ Credits

Created and maintained by Div Sharp  
Originally based on **AcerLinuxManager" and Original Drivers Provided by https://github.com/DetuxTR/AcerNitroLinuxGamingDriver, now reimagined and vastly improved.

---

## AI Disclosure:

This project utilizes AI-generated code (e.g., from Claude) extensively. AI code isn't perfect, and we take no responsibility for its output. Without AI, this project might not exist.
