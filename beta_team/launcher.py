import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import time
from pathlib import Path


def _mean(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))


class BetaTeam:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Beta Team')
        self.root.geometry('700x600')
        self.build_path = tk.StringVar()
        self.repeat_count = tk.IntVar(value=1)
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
        # Notebook with Run and History tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=8, pady=8)

        run_frame = ttk.Frame(notebook)
        history_frame = ttk.Frame(notebook)
        notebook.add(run_frame, text='Run Tests')
        notebook.add(history_frame, text='Benchmark History')

        # ── Run tab ──────────────────────────────────────────────────────────
        tk.Label(run_frame, text='Build Path:').pack(pady=5)
        path_row = tk.Frame(run_frame)
        path_row.pack(fill='x', padx=10)
        tk.Entry(path_row, textvariable=self.build_path, width=60).pack(side='left', expand=True, fill='x')
        tk.Button(path_row, text='Browse', command=self.browse_build).pack(side='left', padx=4)

        # Scenario toggles
        tk.Label(run_frame, text='Scenarios:', font=('Arial', 11, 'bold')).pack(pady=(10, 2))
        for name, var in self.scenarios.items():
            tk.Checkbutton(run_frame, text=name.title(), variable=var).pack(anchor='w', padx=20)

        # Repeat-run control
        repeat_row = tk.Frame(run_frame)
        repeat_row.pack(pady=6)
        tk.Label(repeat_row, text='Repeat runs:').pack(side='left')
        tk.Spinbox(repeat_row, from_=1, to=20, textvariable=self.repeat_count,
                   width=5).pack(side='left', padx=4)
        tk.Label(repeat_row, text='(statistics computed across N runs)',
                 font=('Arial', 9), fg='gray').pack(side='left')

        # Run button
        tk.Button(run_frame, text='🚀 Run Beta Team', command=self.run_tests,
                  bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
                  height=2, width=20).pack(pady=12)

        # Results display
        self.results_text = tk.Text(run_frame, height=14, width=80, font=('Courier', 10))
        scrollbar = tk.Scrollbar(run_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        self.results_text.pack(side='left', pady=6, padx=(10, 0), fill='both', expand=True)
        scrollbar.pack(side='left', fill='y', pady=6)

        # ── History tab ───────────────────────────────────────────────────────
        tk.Label(history_frame, text='Benchmark History (per build)',
                 font=('Arial', 11, 'bold')).pack(pady=8)

        cols = ('Build', 'Runs', 'Mean (s)', 'Std (s)', 'Best (s)', 'Worst (s)', 'Pass Rate', 'Delta')
        self.history_tree = ttk.Treeview(history_frame, columns=cols, show='headings', height=16)
        for col in cols:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=90, anchor='center')
        self.history_tree.pack(fill='both', expand=True, padx=10, pady=4)

        tk.Button(history_frame, text='🔄 Refresh History',
                  command=self.refresh_history).pack(pady=4)

        self.refresh_history()

    def browse_build(self):
        # Support multiple executable formats for cross-platform compatibility
        filetypes = [
            ('Executables', '*.exe *.app *.sh *.bat *.cmd'),
            ('Windows Executables', '*.exe'),
            ('Shell Scripts', '*.sh *.bat *.cmd'),
            ('All Files', '*.*')
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
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
            messagebox.showwarning('No Scenarios Selected', 'Select at least one scenario')
            return

        if not self.build_path.get():
            messagebox.showwarning('No Build Selected', 'Select a build file')
            return

        # Validate build path
        build_file = Path(self.build_path.get())
        if not build_file.exists() or not build_file.is_file():
            messagebox.showwarning('Invalid Build Path', f'Build file does not exist: {build_file}')
            return
        # Allow files without extension for Unix executables (common on Linux/macOS)
        allowed_extensions = ['.exe', '.app', '.sh', '.bat', '.cmd', '']
        if build_file.suffix.lower() not in allowed_extensions:
            messagebox.showwarning('Unsupported File Type', f'Unsupported file type: {build_file.suffix}')
            return

        repeats = max(1, self.repeat_count.get())
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f'Running Beta Team ({repeats} repeat(s))...\n')
        self.root.update()

        # Collect durations per scenario across all repeat runs
        scenario_durations: dict[str, list[float]] = {s: [] for s in selected}
        scenario_passes: dict[str, int] = {s: 0 for s in selected}
        all_run_results: list[list[dict]] = []

        for run_idx in range(repeats):
            if repeats > 1:
                self.results_text.insert(tk.END, f'\n--- Run {run_idx + 1}/{repeats} ---\n')
                self.root.update()

            run_results = []
            for scenario in selected:
                self.results_text.insert(tk.END, f'  Running {scenario}...\n')
                self.root.update()
                result = self.run_robot_test(scenario, self.build_path.get())
                run_results.append(result)
                scenario_durations[scenario].append(result['duration'])
                if result['passed']:
                    scenario_passes[scenario] += 1

            all_run_results.append(run_results)

        benchmarks = self.calculate_benchmarks(
            all_run_results[-1], scenario_durations, scenario_passes, repeats
        )
        self.display_results(benchmarks, scenario_durations, repeats)
        self.save_results(benchmarks)
        self.refresh_history()

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
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            test_duration = time.time() - test_start
            # Use exit code for reliable test result detection (0 = pass, non-zero = fail)
            return {
                'scenario': scenario,
                'passed': result.returncode == 0,
                'duration': test_duration,
                'log': result.stdout
            }
        except FileNotFoundError:
            return {
                'scenario': scenario,
                'passed': False,
                'duration': 0,
                'log': 'Error: Robot Framework not found. Please install with: pip install robotframework'
            }
        except Exception as e:
            return {
                'scenario': scenario,
                'passed': False,
                'duration': 0,
                'log': f'Error running test: {str(e)}'
            }

    def calculate_benchmarks(self, results, scenario_durations, scenario_passes, repeats):
        build_name = Path(self.build_path.get()).stem
        total_time = sum(d for dlist in scenario_durations.values() for d in dlist)
        durations_all = [d for dlist in scenario_durations.values() for d in dlist]
        # Normalize total time by repeats to allow like-for-like comparisons across runs
        repeats_safe = repeats if repeats and repeats > 0 else 1
        mean_time_per_run = total_time / repeats_safe

        stats = {
            'mean_s': round(_mean(durations_all), 3),
            'std_s': round(_std(durations_all), 3),
            'best_s': round(min(durations_all), 3) if durations_all else 0,
            'worst_s': round(max(durations_all), 3) if durations_all else 0,
        }

        total_tests = sum(len(v) for v in scenario_durations.values())
        total_passes = sum(scenario_passes.values())
        pass_rate = round((total_passes / total_tests * 100), 1) if total_tests > 0 else 0.0

        current = {
            'build': build_name,
            'time': total_time,
            'mean_time': mean_time_per_run,
            'repeats': repeats,
            'stats': stats,
            'pass_rate': pass_rate,
            'results': results,
            'delta': 'NEW',
            'scenario_stats': {
                s: {
                    'mean_s': round(_mean(dlist), 3),
                    'std_s': round(_std(dlist), 3),
                    'passes': scenario_passes.get(s, 0),
                    'runs': len(dlist),
                }
                for s, dlist in scenario_durations.items()
            },
        }

        prev = self.prev_results.get(build_name, {})
        if prev:
            # Prefer normalized mean_time if available; fall back to total time for older entries
            prev_mean_time = prev.get('mean_time', prev.get('time'))
            if prev_mean_time and prev_mean_time > 0:
                delta_percent = ((mean_time_per_run - prev_mean_time) / prev_mean_time) * 100
                current['delta'] = f'{delta_percent:+.0f}%'

        # Merge with existing history instead of replacing it
        updated_history = self.prev_results.copy()
        updated_history[build_name] = current
        return updated_history

    def display_results(self, benchmarks, scenario_durations=None, repeats=1):
        self.results_text.insert(tk.END, '\n=== BETA TEAM RESULTS ===\n')
        build_name = Path(self.build_path.get()).stem
        data = benchmarks.get(build_name, {})
        if isinstance(data, dict):
            delta = data.get('delta', 'N/A')
            pass_rate = data.get('pass_rate', 'N/A')
            stats = data.get('stats', {})

            self.results_text.insert(tk.END, f'Build:      {build_name}\n')
            self.results_text.insert(tk.END, f'Repeats:    {repeats}\n')
            self.results_text.insert(tk.END, f'Pass Rate:  {pass_rate}%\n')
            self.results_text.insert(tk.END, f'Delta:      {delta}\n')
            if stats:
                time_line = (
                    f'Time stats: mean={stats.get("mean_s","?")}s  '
                    f'std={stats.get("std_s","?")}s  '
                    f'best={stats.get("best_s","?")}s  '
                    f'worst={stats.get("worst_s","?")}s\n'
                )
                self.results_text.insert(tk.END, time_line)

            scenario_stats = data.get('scenario_stats', {})
            if scenario_stats:
                self.results_text.insert(tk.END, '\nPer-scenario breakdown:\n')
                for scenario, ss in scenario_stats.items():
                    self.results_text.insert(
                        tk.END,
                        f'  {scenario:12s}: {ss["passes"]}/{ss["runs"]} passed  '
                        f'mean={ss["mean_s"]}s  std={ss["std_s"]}s\n'
                    )

    def refresh_history(self):
        """Populate the history Treeview from saved results."""
        self.prev_results = self.load_results()
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for build, data in self.prev_results.items():
            if not isinstance(data, dict):
                continue
            stats = data.get('stats', {})
            self.history_tree.insert('', 'end', values=(
                build,
                data.get('repeats', 1),
                stats.get('mean_s', '?'),
                stats.get('std_s', '?'),
                stats.get('best_s', '?'),
                stats.get('worst_s', '?'),
                f"{data.get('pass_rate', '?')}%",
                data.get('delta', 'NEW'),
            ))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    BetaTeam().run()
