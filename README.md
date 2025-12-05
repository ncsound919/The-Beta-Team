# The-Beta-Team
Agentic Software Beta Testing 

## Beta Team Launcher v2.0

Enhanced UI/UX with menu bar, Go/Stop buttons, status bar for professional beta testing.

### Requirements

- **OS**: Windows
- **Python**: >= 3.10

### Installation

```bash
pip install robotframework robotframework-seleniumlibrary selenium pillow
```

Download ChromeDriver matching your Chrome version from [chromedriver.chromium.org](https://chromedriver.chromium.org/)

### Project Structure

```
beta_team/
├── launcher.py           # Enhanced UI dashboard
├── tests/
│   ├── onboarding.robot  # First time user onboarding tests
│   ├── poweruser.robot   # Power user workflow tests
│   └── edgecases.robot   # Edge case testing
├── builds/               # Place your build files here
├── reports/              # Test reports output
├── results.json          # Test results (auto-generated)
└── beta.json             # Configuration file
```

### Setup Steps

1. Navigate to the `beta_team/` folder
2. Install dependencies: `pip install robotframework robotframework-seleniumlibrary selenium pillow`
3. Download ChromeDriver from [chromedriver.chromium.org](https://chromedriver.chromium.org/)
4. Run the launcher: `python launcher.py`
5. File → Load Build → Check scenarios → GO!

### UI Features

- 📋 **Menu bar**: File/Tests/Help
- 🚀 **Big GO button**: Starts threaded tests
- ⏹ **STOP button**: Interrupts running tests
- 📊 **Live progress bar + status**
- ✨ **Dark theme professional UX**
- 📝 **Timestamped scrolling log**
- ✅ **Real-time pass/fail feedback**
