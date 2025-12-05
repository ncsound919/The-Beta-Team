import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import os
import time
import threading
from pathlib import Path

class BetaTeam:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Beta Team - Professional Testing Suite')
        self.root.geometry('800x700')
        self.root.configure(bg='#2b2b2b')

        self.build_path = tk.StringVar()
        self.scenarios = {
            'onboarding': tk.BooleanVar(),
            'poweruser': tk.BooleanVar(),
            'edgecases': tk.BooleanVar()
        }
        self.is_running = False
        self.stop_event = threading.Event()
        self.prev_results = self.load_results()
        self.build_ui()

    def build_ui(self):
        # Menu Bar
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

        # Main Frame
        main_frame = ttk.Frame(self.root, padding='20')
        main_frame.pack(fill='both', expand=True)

        # Header
        header = ttk.Label(main_frame, text='🚀 Beta Team', font=('Arial', 20, 'bold'))
        header.pack(pady=(0,20))

        # Build Selection
        build_frame = ttk.LabelFrame(main_frame, text='Build Selection', padding='10')
        build_frame.pack(fill='x', pady=(0,15))
        ttk.Label(build_frame, text='Build Path:').pack(anchor='w')
        path_frame = ttk.Frame(build_frame)
        path_frame.pack(fill='x', pady=(5,0))
        ttk.Entry(path_frame, textvariable=self.build_path, width=60).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text='Browse', command=self.browse_build).pack(side='right', padx=(5,0))

        # Scenarios
        scenarios_frame = ttk.LabelFrame(main_frame, text='Test Scenarios', padding='10')
        scenarios_frame.pack(fill='x', pady=(0,15))
        for name, var in self.scenarios.items():
            ttk.Checkbutton(scenarios_frame, text=name.title(), variable=var).pack(anchor='w', pady=2)

        # Control Buttons
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(pady=20)
        self.go_btn = ttk.Button(controls_frame, text='🚀 GO', command=self.start_tests,
                                style='Accent.TButton', width=12)
        self.go_btn.pack(side='left', padx=(0,10))
        
        self.stop_btn = ttk.Button(controls_frame, text='⏹ STOP', command=self.stop_tests,
                                  state='disabled', width=12)
        self.stop_btn.pack(side='left')
        
        ttk.Button(controls_frame, text='Clear Log', command=self.clear_log).pack(side='left', padx=(10,0))

        # Progress & Status
        progress_frame = ttk.LabelFrame(main_frame, text='Progress', padding='10')
        progress_frame.pack(fill='x', pady=(0,15))
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0,10))
        
        self.status_label = ttk.Label(progress_frame, text='Ready to test', foreground='green')
        self.status_label.pack()

        # Results Log
        results_frame = ttk.LabelFrame(main_frame, text='Live Results', padding='10')
        results_frame.pack(fill='both', expand=True)
        self.results_text = tk.Text(results_frame, bg='#1e1e1e', fg='#ffffff', height=12,
                                   font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.results_text.insert(tk.END, f'[{timestamp}] {message}\n')
        self.results_text.see(tk.END)
        self.root.update()

    def browse_build(self):
        path = filedialog.askopenfilename(filetypes=[('Executables', '*.exe'), ('All', '*.*')])
        if path:
            self.build_path.set(path)
            self.log(f'Loaded build: {Path(path).name}')

    def load_results(self):
        try:
            with open('results.json', 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_results_manually(self):
        self.save_results(self.prev_results)
        self.log('Results saved manually')

    def start_tests(self):
        selected = [k for k,v in self.scenarios.items() if v.get()]
        if not selected:
            messagebox.showwarning('No scenarios', 'Select at least one scenario')
            return
        if not self.build_path.get():
            messagebox.showwarning('No build', 'Select a build file')
            return

        self.is_running = True
        self.stop_event.clear()
        self.go_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.start()
        self.status_label.config(text='Testing in progress...', foreground='orange')
        
        # Run in thread
        thread = threading.Thread(target=self.run_tests_thread, args=(selected,))
        thread.daemon = True
        thread.start()

    def stop_tests(self):
        self.stop_event.set()
        self.log('STOP requested...')

    def run_tests_thread(self, selected):
        try:
            start_time = time.time()
            all_results = []

            for i, scenario in enumerate(selected):
                if self.stop_event.is_set():
                    self.log('Tests stopped by user')
                    break
                
                self.log(f'Running {scenario}... ({i+1}/{len(selected)})')
                result = self.run_robot_test(scenario, self.build_path.get())
                all_results.append(result)

            if not self.stop_event.is_set():
                total_time = time.time() - start_time
                benchmarks = self.calculate_benchmarks(all_results, total_time)
                self.display_results(benchmarks)
                self.save_results(benchmarks)
        finally:
            self.tests_complete()

    def tests_complete(self):
        self.root.after(0, self._tests_complete_ui)

    def _tests_complete_ui(self):
        self.is_running = False
        self.go_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.status_label.config(text='Tests complete ✅', foreground='green')

    def run_robot_test(self, scenario, build_path):
        cmd = [
            'robot',
            '--variable', f'BUILD_PATH:{build_path}',
            f'tests/{scenario}.robot',
            '--outputdir', 'reports',
            '--report', 'NONE',
            '--log', f'{scenario}.log.html'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        passed = 'PASS' in result.stdout
        self.log(f'{scenario}: {"✅ PASS" if passed else "❌ FAIL"}')
        return {
            'scenario': scenario,
            'passed': passed,
            'duration': time.time(),
            'log': result.stdout
        }

    def calculate_benchmarks(self, results, total_time):
        build_name = Path(self.build_path.get()).stem
        current = {'build': build_name, 'time': total_time, 'results': results}
        prev = self.prev_results.get(build_name, {})
        prev_time = prev.get('time', 1) if prev else 1
        delta = 'NEW' if not prev else f'{((total_time - prev_time) / prev_time * 100):+.0f}%'
        result = {build_name: current, 'delta': delta}
        self.prev_results = result
        return result

    def display_results(self, benchmarks):
        self.log('=== BETA TEAM RESULTS ===')
        delta = benchmarks.get('delta', '')
        for build, data in benchmarks.items():
            if build != 'delta':
                passed_count = len([r for r in data['results'] if r['passed']])
                total = len(data['results'])
                self.log(f'{build}: {delta} | {passed_count}/{total} passed')

    def save_results(self, results):
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=2)

    def clear_log(self):
        self.results_text.delete(1.0, tk.END)

    def open_reports(self):
        import sys
        import webbrowser
        reports_path = os.path.abspath('reports')
        if sys.platform == 'win32':
            os.startfile(reports_path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', reports_path])
        else:
            webbrowser.open(f'file://{reports_path}')

    def clear_results(self):
        if messagebox.askyesno('Clear', 'Clear all results?'):
            self.prev_results = {}
            if os.path.exists('results.json'):
                os.remove('results.json')
            self.log('Results cleared')

    def show_about(self):
        messagebox.showinfo('About', 'Beta Team v2.0\nLocal AI-powered beta testing suite')

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    BetaTeam().run()
