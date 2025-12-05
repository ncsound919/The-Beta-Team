# The-Beta-Team

Agentic Software Beta Testing - Local open-source beta testing dashboard for desktop/web apps with menu toggles, benchmarks, and deltas.

## Beta Team Launcher

A comprehensive beta testing dashboard with Robot Framework integration for automated testing scenarios.

### Requirements

- **OS**: Windows
- **Python**: >= 3.10

### Installation

```bash
# Install required packages
pip install robotframework robotframework-seleniumlibrary pillow selenium

# Optional: Install via chocolatey
choco install robotframework

# Download ChromeDriver matching your Chrome version
# https://chromedriver.chromium.org/
```

### Project Structure

```
beta_team/
├── launcher.py          # Main dashboard
├── tests/               # Robot Framework test suites
│   ├── onboarding.robot
│   ├── poweruser.robot
│   └── edgecases.robot
├── builds/              # Drop your EXEs here
├── reports/             # Auto-generated HTML/JSON
├── results.json         # Benchmark history
└── beta.json            # Build manifest
```

### Setup Steps

1. Clone the repository
2. Navigate to `beta_team/` folder
3. Run `pip install robotframework robotframework-seleniumlibrary selenium pillow`
4. Download ChromeDriver matching your Chrome version
5. Drop your EXE in `builds/` folder
6. Run `python launcher.py`
7. Browse build → toggle scenarios → Run Beta Team

### Usage

| Action | Description |
|--------|-------------|
| Drop build | Put EXE in `builds/` or browse any path |
| Toggle scenarios | Check onboarding/poweruser/edgecases |
| Run | Click 🚀 Run Beta Team → watch live results |
| Benchmarks | Auto-compares timing vs previous build |
| Extend | Add more .robot files to `tests/`, they'll auto-appear |

### Customization

- Replace SeleniumLibrary with AppiumLibrary for native desktop apps
- Add Windows Agent Arena tasks via subprocess calls
- Extend benchmarks: add screenshots, memory usage, crash detection
- Add CI: `python launcher.py --headless --build v1.2.exe`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `robot` not found | Run `pip install robotframework` |
| ChromeDriver error | Match ChromeDriver version to your Chrome |
| No tests run | Check `tests/*.robot` files exist and are valid Robot syntax |
