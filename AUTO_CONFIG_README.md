# 🚀 Auto-Configuration Feature

This project now includes **automatic Chrome detection and configuration** that allows you to use your local Chrome browser for automation instead of launching separate Playwright browser instances.

## ✨ Features

### 🔍 Automatic Chrome Detection
- **Auto-detects** Chrome installation paths on Windows
- **Searches multiple locations**:
  - `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
  - `C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe`
  - Windows Registry entries
  - System PATH using `where chrome` command

### 🎯 Smart Configuration
- **Automatically sets** environment variables:
  - `BROWSER_PATH`: Chrome executable path
  - `USE_OWN_BROWSER`: Set to `true` when Chrome is detected
  - `BROWSER_USER_DATA`: Chrome user data directory
- **Tests Chrome functionality** before enabling
- **Falls back to Playwright** if Chrome detection fails

### 🌐 Browser Integration
- **Uses your existing Chrome** for all automation tasks
- **Preserves your browser data** (cookies, bookmarks, extensions)
- **Maintains login sessions** across automation runs
- **No need to re-login** to websites

## 🚀 How It Works

### 1. Startup Detection
When you run the web UI:
```bash
python webui.py --ip 127.0.0.1 --port 7788
```

The system automatically:
1. 🔍 **Scans for Chrome installations**
2. ✅ **Tests Chrome functionality**
3. ⚙️ **Configures environment variables**
4. 💾 **Saves configuration** to `chrome_auto_config.json`

### 2. Browser Settings Integration
The **Browser Settings** tab now shows:
- ✅ **Auto-detection status**
- 📍 **Chrome path** (auto-filled)
- 📁 **User data directory** (auto-filled)
- 🔧 **Configuration status**

### 3. Agent Execution
When you run an agent task:
- 🎯 **Uses your local Chrome** if detected
- 📱 **Falls back to Playwright** if Chrome unavailable
- 🔄 **Preserves browser state** between tasks

## 📋 Usage

### Basic Usage
1. **Start the web UI**:
   ```bash
   python webui.py --ip 127.0.0.1 --port 7788
   ```

2. **Open in browser**: `http://127.0.0.1:7788`

3. **Check Browser Settings tab**:
   - See auto-detection status
   - Verify Chrome path is set
   - Confirm "Use Own Browser" is enabled

4. **Run agent tasks**:
   - Go to "Run Agent" tab
   - Enter your task
   - Click "Submit Task"
   - Watch automation in your Chrome browser!

### Advanced Configuration

#### Disable Auto-Configuration
```bash
python webui.py --ip 127.0.0.1 --port 7788 --no-auto-config
```

#### Manual Configuration
If auto-detection fails, you can manually set:
- **Browser Binary Path**: Path to your Chrome executable
- **Browser User Data Dir**: Path to Chrome user data
- **Use Own Browser**: Check to enable local Chrome

## 🔧 Technical Details

### Auto-Configuration Files
- **`chrome_auto_config.json`**: Saved configuration
- **`src/utils/chrome_detector.py`**: Chrome detection logic
- **`src/utils/auto_config.py`**: Configuration management

### Environment Variables
The system sets these environment variables:
```bash
BROWSER_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
USE_OWN_BROWSER=true
BROWSER_USER_DATA=C:\Users\{username}\AppData\Local\Google\Chrome\User Data
```

### Detection Methods
1. **Common Paths**: Checks standard Chrome installation locations
2. **Registry**: Searches Windows registry for Chrome paths
3. **System PATH**: Uses `where chrome` command
4. **User Data**: Automatically finds Chrome user data directory

## 🧪 Testing

### Test Auto-Configuration
```bash
python test_auto_config.py
```

### Demo Automation
```bash
python demo_auto_config.py
```

## 🐛 Troubleshooting

### Chrome Not Detected
1. **Check Chrome installation**: Ensure Chrome is installed
2. **Verify paths**: Check if Chrome exists in common locations
3. **Manual configuration**: Set browser path manually in settings

### Chrome Test Fails
1. **Check permissions**: Ensure Chrome can be launched
2. **Update Chrome**: Try updating to latest version
3. **Fallback to Playwright**: System will automatically use Playwright

### Browser Settings Not Updated
1. **Refresh page**: Reload the web UI
2. **Check logs**: Look for auto-configuration messages
3. **Manual refresh**: Click "Clear" and try again

## 📊 Status Indicators

### Browser Settings Tab
- ✅ **Chrome Detected**: Yes/No
- 📍 **Chrome Path**: Auto-detected path
- 📁 **User Data Directory**: Auto-detected directory
- 🌐 **Using Local Chrome**: Yes/No
- 🔧 **Connection Tested**: Yes/No

### Console Logs
Look for these messages:
```
INFO     [__main__] Starting automatic Chrome configuration...
INFO     [src.utils.chrome_detector] Found Chrome at: C:\Program Files\Google\Chrome\Application\chrome.exe
INFO     [src.utils.auto_config] Chrome basic test successful
INFO     [__main__] ✅ Using local Chrome browser for automation
```

## 🎉 Benefits

### For Users
- 🚀 **No manual configuration** required
- 🔐 **Preserves login sessions** and cookies
- 📚 **Keeps bookmarks and extensions**
- 🎯 **Uses familiar browser interface**

### For Developers
- 🔧 **Automatic setup** reduces configuration overhead
- 🧪 **Easy testing** with local browser
- 📊 **Better debugging** with visible browser actions
- 🔄 **Seamless integration** with existing workflows

## 🔮 Future Enhancements

- 🔍 **Multi-browser support** (Firefox, Edge, Safari)
- 🎨 **Custom browser profiles** for different automation tasks
- 📱 **Mobile browser support** via remote debugging
- 🔐 **Enhanced security** with isolated browser profiles
- 📊 **Performance monitoring** and optimization

---

**🎉 Enjoy automated browser tasks with your local Chrome browser!** 