import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import json
import os
import time
from pathlib import Path


class BetaTeam:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Beta Team')
        self.root.geometry('600x500')
        self.build_path = tk.StringVar()
        self.scenarios = {
            'onboarding': tk.BooleanVar(),
            'poweruser': tk.BooleanVar(),
            'edgecases': tk.BooleanVar()
        }
        # Get the directory where the script is located
        self.script_dir = Path(__file__).parent.resolve()
        self.results_file = self.script_dir / 'results.json'
        self.prev_results = self.load_results()
        self.build_ui()

    def build_ui(self):
        # Build path
        tk.Label(self.root, text='Build Path:').pack(pady=5)
        tk.Entry(self.root, textvariable=self.build_path, width=70).pack()
        tk.Button(self.root, text='Browse', command=self.browse_build).pack()

        # Scenario toggles
        tk.Label(self.root, text='Scenarios:', font=('Arial', 12, 'bold')).pack(pady=10)
        for name, var in self.scenarios.items():
            tk.Checkbutton(self.root, text=name.title(), variable=var).pack(anchor='w', padx=20)

        # Run button
        tk.Button(self.root, text='🚀 Run Beta Team', command=self.run_tests,
                  bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
                  height=2, width=20).pack(pady=20)

        # Results display
        self.results_text = tk.Text(self.root, height=15, width=70)
        self.results_text.pack(pady=10, padx=10, fill='both', expand=True)

    def browse_build(self):
        path = filedialog.askopenfilename(filetypes=[('Executables', '*.exe'), ('All', '*.*')])
        if path:
            self.build_path.set(path)

    def load_results(self):
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_results(self, results):
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def run_tests(self):
        selected = [k for k, v in self.scenarios.items() if v.get()]
        if not selected:
            messagebox.showwarning('No scenarios', 'Select at least one scenario')
            return

        if not self.build_path.get():
            messagebox.showwarning('No build', 'Select a build file')
            return

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, 'Running Beta Team...\n')
        self.root.update()

        start_time = time.time()
        all_results = []

        for scenario in selected:
            self.results_text.insert(tk.END, f'Running {scenario}...\n')
            self.root.update()

            result = self.run_robot_test(scenario, self.build_path.get())
            all_results.append(result)

        total_time = time.time() - start_time
        benchmarks = self.calculate_benchmarks(all_results, total_time)
        self.display_results(benchmarks)
        self.save_results(benchmarks)

    def run_robot_test(self, scenario, build_path):
        tests_dir = self.script_dir / 'tests'
        reports_dir = self.script_dir / 'reports'
        cmd = [
            'robot',
            '--variable', f'BUILD_PATH:{build_path}',
            str(tests_dir / f'{scenario}.robot'),
            '--outputdir', str(reports_dir),
            '--report', 'NONE',
            '--log', f'{scenario}.log.html'
        ]
        test_start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        test_duration = time.time() - test_start
        return {
            'scenario': scenario,
            'passed': 'PASS' in result.stdout,
            'duration': test_duration,
            'log': result.stdout
        }

    def calculate_benchmarks(self, results, total_time):
        build_name = Path(self.build_path.get()).stem
        current = {'build': build_name, 'time': total_time, 'results': results, 'delta': 'NEW'}
        prev = self.prev_results.get(build_name, {})

        if prev:
            prev_time = prev.get('time', 1)
            if prev_time > 0:
                delta_percent = ((total_time - prev_time) / prev_time) * 100
                current['delta'] = f'{delta_percent:+.0f}%'

        return {build_name: current, 'delta': current['delta']}

    def display_results(self, benchmarks):
        self.results_text.insert(tk.END, '\n=== BETA TEAM RESULTS ===\n')
        for build, data in benchmarks.items():
            if build != 'delta' and isinstance(data, dict):
                passed_count = len([r for r in data.get('results', []) if r.get('passed')])
                total_count = len(data.get('results', []))
                delta = data.get('delta', 'N/A')
                self.results_text.insert(tk.END, f'{build}: {delta} time change | {passed_count}/{total_count} passed\n')

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    BetaTeam().run()
