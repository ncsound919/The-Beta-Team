"""Beta Team Launcher v3.0 - Professional UI + Humanized feedback + Dev action items"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import os
import sys
import threading
from pathlib import Path

# Default feedback rules - used as fallback if feedback_rules.json is not found
_FEEDBACK_RULES = {
    'timeout': {
        'human': "User waited too long for '{element}' to appear. Feels stuck and frustrated.",
        'dev': "Add loading spinner. Check if {element} exists in DOM. Increase timeout or optimize backend query."
    },
    'element_not_found': {
        'human': "Couldn't find '{element}' button/field. User can't complete the task.",
        'dev': "Verify '{element}' selector exists in latest build. Check CSS changes broke locator. Add data-testid."
    },
    'invalid_email': {
        'human': "Email validation rejected '{email}'. User confused about format rules.",
        'dev': "Add inline validation message explaining format. Show example 'user@domain.com'. Handle @@ gracefully."
    },
    'no_welcome': {
        'human': "No 'Welcome' message after signup. User thinks signup failed.",
        'dev': "Verify success state renders 'Welcome' text. Check API response. Add fallback success indicator."
    },
    'general_fail': {
        'human': "Something broke during '{scenario}'. User experience interrupted.",
        'dev': "Check {scenario} logs in reports/{scenario}.log.html. Add more specific assertions. Screenshot failure state."
    },
    'robot_not_installed': {
        'human': "Test automation tool is not available. Cannot run tests.",
        'dev': "Robot Framework is not installed or not in PATH. Run: pip install robotframework robotframework-seleniumlibrary"
    },
    'test_file_missing': {
        'human': "Test scenario '{scenario}' cannot be found. Unable to run this test.",
        'dev': "Create test file at tests/{scenario}.robot or remove scenario from launcher."
    }
}


class BetaTeam:
    """Main Beta Team application class with UI and test execution."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Beta Team v3.0 - Humanized Feedback')
        self.root.geometry('900x800')
        self.root.configure(bg='#2b2b2b')
        self.build_path = tk.StringVar()
        self.scenarios = {
            'onboarding': tk.BooleanVar(),
            'poweruser': tk.BooleanVar(),
            'edgecases': tk.BooleanVar()
        }
        self.is_running = False
        self.stop_event = threading.Event()
        self.current_process = None  # Track running subprocess for stop capability
        self.prev_results = self.load_results()
        self.feedback_rules = self.load_feedback_rules()
        self.build_ui()

    def build_ui(self):
        """Build the main user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Load Build...', command=self.browse_build)
        file_menu.add_command(label='Save Results', command=self.save_results_manually)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)

        test_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Tests', menu=test_menu)
        test_menu.add_command(label='View Reports', command=self.open_reports)
        test_menu.add_command(label='Clear Results', command=self.clear_results)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About', command=self.show_about)

        main_frame = ttk.Frame(self.root, padding='20')
        main_frame.pack(fill='both', expand=True)

        header = ttk.Label(main_frame, text='🚀 Beta Team v3.0', font=('Arial', 20, 'bold'))
        header.pack(pady=(0, 20))

        # Build Selection
        build_frame = ttk.LabelFrame(main_frame, text='Build Selection', padding='10')
        build_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(build_frame, text='Build Path:').pack(anchor='w')
        path_frame = ttk.Frame(build_frame)
        path_frame.pack(fill='x', pady=(5, 0))
        ttk.Entry(path_frame, textvariable=self.build_path, width=60).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text='Browse', command=self.browse_build).pack(side='right', padx=(5, 0))

        # Scenarios Selection
        scenarios_frame = ttk.LabelFrame(main_frame, text='Test Scenarios', padding='10')
        scenarios_frame.pack(fill='x', pady=(0, 15))
        for name, var in self.scenarios.items():
            ttk.Checkbutton(scenarios_frame, text=name.title(), variable=var).pack(anchor='w', pady=2)

        # Control Buttons
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(pady=20)
        self.go_btn = ttk.Button(controls_frame, text='🚀 GO', command=self.start_tests, width=12)
        self.go_btn.pack(side='left', padx=(0, 10))
        self.stop_btn = ttk.Button(controls_frame, text='⏹ STOP', command=self.stop_tests, state='disabled', width=12)
        self.stop_btn.pack(side='left')
        ttk.Button(controls_frame, text='Clear Log', command=self.clear_log).pack(side='left', padx=(10, 0))

        # Feedback Tabs
        feedback_frame = ttk.LabelFrame(main_frame, text='Feedback & Action Items', padding='10')
        feedback_frame.pack(fill='both', expand=True)

        notebook = ttk.Notebook(feedback_frame)
        notebook.pack(fill='both', expand=True)

        # Human feedback tab
        human_frame = ttk.Frame(notebook)
        notebook.add(human_frame, text='👤 User Experience')
        self.human_text = tk.Text(human_frame, bg='#1e1e1e', fg='#00ff00', height=15, font=('Arial', 11))
        scrollbar_h = ttk.Scrollbar(human_frame, orient='vertical', command=self.human_text.yview)
        self.human_text.configure(yscrollcommand=scrollbar_h.set)
        self.human_text.pack(side='left', fill='both', expand=True)
        scrollbar_h.pack(side='right', fill='y')

        # Dev action tab
        dev_frame = ttk.Frame(notebook)
        notebook.add(dev_frame, text='🔧 Dev Fixes')
        self.dev_text = tk.Text(dev_frame, bg='#1e1e1e', fg='#ffaa00', height=15, font=('Arial', 11))
        scrollbar_d = ttk.Scrollbar(dev_frame, orient='vertical', command=self.dev_text.yview)
        self.dev_text.configure(yscrollcommand=scrollbar_d.set)
        self.dev_text.pack(side='left', fill='both', expand=True)
        scrollbar_d.pack(side='right', fill='y')

    def parse_log_for_issues(self, log_text, scenario):
        """Parse test log output for issues and generate humanized feedback."""
        issues = []
        log_lower = log_text.lower()

        # Pattern matching common failures
        if 'timeout' in log_lower:
            issues.append(self.get_feedback('timeout', scenario, element='page element'))
        if 'not found' in log_lower or 'no such element' in log_lower:
            issues.append(self.get_feedback('element_not_found', scenario, element='critical button'))
        if 'invalid email' in log_lower:
            issues.append(self.get_feedback('invalid_email', scenario, email='testuser@beta.com'))
        # Only flag missing welcome if test explicitly failed on welcome assertion
        # Robot Framework uses 'FAIL :' pattern for failed test assertions
        if ('page should contain' in log_lower and 'welcome' in log_lower and
                ('fail :' in log_lower or '| fail |' in log_lower)):
            issues.append(self.get_feedback('no_welcome', scenario))

        return issues if issues else [self.get_feedback('general_fail', scenario)]

    def get_feedback(self, issue_type, scenario, *, element='UI', email=''):
        """
        Get feedback messages for a specific issue type.

        Parameters
        ----------
        issue_type : str
            The type of issue (e.g., 'timeout', 'element_not_found', 'invalid_email').
        scenario : str
            The scenario name (e.g., 'onboarding', 'poweruser').
        element : str, keyword-only, optional
            The UI element involved in the issue. Used for 'timeout', 'element_not_found'.
        email : str, keyword-only, optional
            The email address involved. Used for 'invalid_email'.

        Returns
        -------
        dict
            A dictionary with keys 'type', 'human', and 'dev' containing feedback messages.

        Examples
        --------
        >>> self.get_feedback('timeout', 'onboarding', element='submit button')
        >>> self.get_feedback('invalid_email', 'signup', email='bad@address')
        """
        rule = self.feedback_rules.get(issue_type) or self.feedback_rules.get('general_fail') or _FEEDBACK_RULES['general_fail']
        # Use format_map with defaults to handle missing placeholders gracefully
        format_values = {
            'scenario': scenario.title(),
            'element': element,
            'email': email
        }
        human_msg = rule['human'].format_map(format_values)
        dev_msg = rule['dev'].format_map(format_values)
        return {'type': issue_type, 'human': human_msg, 'dev': dev_msg}

    def log_human_feedback(self, issues):
        """Display human-readable feedback in the User Experience tab."""
        self.human_text.delete(1.0, tk.END)
        for issue in issues:
            self.human_text.insert(tk.END, f'💥 {issue["human"]}\n\n')

    def log_dev_feedback(self, issues):
        """Display developer action items in the Dev Fixes tab."""
        self.dev_text.delete(1.0, tk.END)
        for issue in issues:
            self.dev_text.insert(tk.END, f'⚡ FIX: {issue["dev"]}\n\n')

    def run_robot_test(self, scenario, build_path):
        """Execute a Robot Framework test for the given scenario."""
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)

        # Check if test file exists before attempting to run
        test_path = Path(__file__).parent / f'tests/{scenario}.robot'
        if not test_path.exists():
            issues = [self.get_feedback('test_file_missing', scenario)]
            self.root.after(0, lambda i=issues: self.log_human_feedback(i))
            self.root.after(0, lambda i=issues: self.log_dev_feedback(i))
            return {'scenario': scenario, 'passed': False, 'issues': issues}

        cmd = [
            'robot',
            '--variable', f'BUILD_PATH:{build_path}',
            str(test_path),
            '--outputdir', str(reports_dir),
            '--report', 'NONE',
            '--log', f'{scenario}.log.html'
        ]

        try:
            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=Path(__file__).parent
            )
            try:
                stdout, stderr = self.current_process.communicate(timeout=300)
                passed = self.current_process.returncode == 0
            finally:
                self.current_process = None

            # Parse for humanized feedback
            issues = self.parse_log_for_issues(stdout + stderr, scenario)
            self.root.after(0, lambda i=issues: self.log_human_feedback(i))
            self.root.after(0, lambda i=issues: self.log_dev_feedback(i))

            return {'scenario': scenario, 'passed': passed, 'issues': issues}
        except subprocess.TimeoutExpired:
            if self.current_process:
                self.current_process.kill()
                self.current_process = None
            issues = [self.get_feedback('timeout', scenario, element='test execution')]
            self.root.after(0, lambda i=issues: self.log_human_feedback(i))
            self.root.after(0, lambda i=issues: self.log_dev_feedback(i))
            return {'scenario': scenario, 'passed': False, 'issues': issues}
        except FileNotFoundError:
            issues = [self.get_feedback('robot_not_installed', scenario)]
            self.root.after(0, lambda i=issues: self.log_human_feedback(i))
            self.root.after(0, lambda i=issues: self.log_dev_feedback(i))
            return {'scenario': scenario, 'passed': False, 'issues': issues}

    def browse_build(self):
        """Open file dialog to select build executable."""
        path = filedialog.askopenfilename(filetypes=[('Executables', '*.exe'), ('All', '*.*')])
        if path:
            self.build_path.set(path)

    def load_results(self):
        """Load previous test results from JSON file."""
        results_path = Path(__file__).parent / 'results.json'
        try:
            with open(results_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def load_feedback_rules(self):
        """Load feedback rules from JSON file or use defaults."""
        rules_path = Path(__file__).parent / 'feedback_rules.json'
        try:
            with open(rules_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return _FEEDBACK_RULES

    def save_results(self, results):
        """Save test results to JSON file."""
        results_path = Path(__file__).parent / 'results.json'
        try:
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
        except OSError as e:
            messagebox.showerror('Error', f'Failed to save results: {e}')

    def save_results_manually(self):
        """Manually trigger results save."""
        self.save_results(self.prev_results)
        messagebox.showinfo('Saved', 'Results saved successfully!')

    def start_tests(self):
        """Start running selected test scenarios."""
        if not self.build_path.get():
            messagebox.showwarning('Warning', 'Please select a build path first.')
            return

        selected = [name for name, var in self.scenarios.items() if var.get()]
        if not selected:
            messagebox.showwarning('Warning', 'Please select at least one test scenario.')
            return

        self.is_running = True
        self.stop_event.clear()
        self.go_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        def run_tests():
            results = {}
            for scenario in selected:
                if self.stop_event.is_set():
                    break
                result = self.run_robot_test(scenario, self.build_path.get())
                results[scenario] = result

            # Update results on main thread to avoid race conditions
            def update_results_on_main_thread():
                self.prev_results = results
                self.save_results(results)
                self._tests_completed()

            self.root.after(0, update_results_on_main_thread)

        thread = threading.Thread(target=run_tests)
        thread.daemon = True
        thread.start()

    def _tests_completed(self):
        """Callback when tests complete."""
        self.is_running = False
        self.go_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def stop_tests(self):
        """Stop running tests and terminate any running subprocess."""
        self.stop_event.set()
        if self.current_process:
            try:
                self.current_process.terminate()
            except ProcessLookupError:
                pass  # Process has already finished

    def clear_log(self):
        """Clear all feedback logs."""
        self.human_text.delete(1.0, tk.END)
        self.dev_text.delete(1.0, tk.END)

    def clear_results(self):
        """Clear stored results."""
        self.prev_results = {}
        self.save_results({})
        messagebox.showinfo('Cleared', 'Results cleared!')

    def open_reports(self):
        """Open reports directory."""
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        if os.name == 'nt':
            os.startfile(reports_dir)
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(reports_dir)], check=False)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', str(reports_dir)], check=False)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            'About Beta Team v3.0',
            'Beta Team Launcher v3.0\n\n'
            'Professional UI + Humanized feedback\n'
            '+ Dev action items for every issue\n\n'
            'Features:\n'
            '👤 User Experience tab: Plain English feedback\n'
            '🔧 Dev Fixes tab: Actionable fixes\n'
            '🧠 Smart parsing: Detects issues automatically'
        )

    def run(self):
        """Start the main application loop."""
        self.root.mainloop()


if __name__ == '__main__':
    BetaTeam().run()
