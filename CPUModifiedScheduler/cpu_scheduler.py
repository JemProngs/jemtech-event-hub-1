import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import math
import psutil
import platform
from datetime import datetime
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches

# Initialize pygame for sound effects
pygame.mixer.init()


# Process of our program
class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=1):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time
        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.start_time = None
        self.execution_log = []
        self.response_time = 0  # New metric for analysis


# Part of the GUI
class SystemUtilitiesDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive CPU Scheduler Simulator")
        self.geometry("1500x950")
        self.configure(bg="#0f1524")
        self.processes = []
        self.colors = {}
        self.time_quantum = tk.IntVar(value=2)
        self.current_tab = "scheduler"
        self.system_stats = {}
        self.music_playing = False
        self.current_music = None
        self.algorithm_stats = {}  # Store algorithm performance metrics
        self.sound_effects = {}  # Store sound effects
        self.animation = None  # For matplotlib animation
        self.current_time = 0  # For animation

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create frames for different tabs
        self.scheduler_frame = ttk.Frame(self.notebook)
        self.system_monitor_frame = ttk.Frame(self.notebook)
        self.process_manager_frame = ttk.Frame(self.notebook)
        self.analysis_frame = ttk.Frame(self.notebook)  # New analysis tab

        self.notebook.add(self.scheduler_frame, text="CPU Scheduler")
        self.notebook.add(self.system_monitor_frame, text="System Monitor")
        self.notebook.add(self.process_manager_frame, text="Process Manager")
        self.notebook.add(self.analysis_frame, text="Performance Analysis")  # Add analysis tab

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Set a futuristic theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # Load sound effects
        self.load_sound_effects()

        # Create the scheduler UI
        self.create_scheduler_ui()

        # Create system monitor UI
        self.create_system_monitor_ui()

        # Create process manager UI
        self.create_process_manager_ui()

        # Create analysis UI
        self.create_analysis_ui()

        # Start system monitoring
        self.update_system_stats()

    def load_sound_effects(self):
        """Load or generate sound effects"""
        try:
            # Generate simple sound effects programmatically
            self.generate_beep_sound("high", 1000)  # High pitch beep
            self.generate_beep_sound("medium", 600)  # Medium pitch beep
            self.generate_beep_sound("low", 300)  # Low pitch beep
            self.generate_beep_sound("complete", 800, duration=0.5)  # Completion sound
        except:
            print("Could not generate sound effects")

    def generate_beep_sound(self, name, frequency, duration=0.1):
        """Generate a simple beep sound"""
        sample_rate = 44100
        n_samples = int(round(duration * sample_rate))
        buf = np.zeros((n_samples, 2), dtype=np.float32)
        max_amplitude = 32767  # For 16-bit audio

        # Generate a sine wave
        for s in range(n_samples):
            t = float(s) / sample_rate
            buf[s][0] = math.sin(2 * math.pi * frequency * t) * max_amplitude
            buf[s][1] = math.sin(2 * math.pi * frequency * t) * max_amplitude

        # Convert to pygame sound
        sound = pygame.sndarray.make_sound(buf)
        self.sound_effects[name] = sound

    def play_sound(self, name):
        """Play a sound effect by name"""
        if name in self.sound_effects:
            self.sound_effects[name].play()

    def configure_styles(self):
        self.style.configure('TFrame', background='#0f1524')
        self.style.configure('TLabel', background='#0f1524', foreground='#00e6ff', font=('Arial', 10))
        self.style.configure('TButton', background='#1a2337', foreground='#00e6ff',
                             font=('Arial', 10, 'bold'), borderwidth=1)
        self.style.map('TButton', background=[('active', '#243b55')])
        self.style.configure('TRadiobutton', background='#0f1524', foreground='#00e6ff',
                             font=('Arial', 10))
        self.style.configure('Treeview', background='#1a2337', foreground='#00e6ff',
                             fieldbackground='#1a2337', font=('Arial', 9))
        self.style.configure('Treeview.Heading', background='#243b55', foreground='#00e6ff',
                             font=('Arial', 10, 'bold'))
        self.style.configure('TEntry', fieldbackground='#1a2337', foreground='#00e6ff',
                             font=('Arial', 10))
        self.style.configure('TNotebook', background='#0f1524', borderwidth=0)
        self.style.configure('TNotebook.Tab', background='#1a2337', foreground='#00e6ff',
                             padding=[10, 5], font=('Arial', 10, 'bold'))
        self.style.map('TNotebook.Tab', background=[('selected', '#243b55')])

    def create_scheduler_ui(self):
        # Header with futuristic title
        header_frame = ttk.Frame(self.scheduler_frame)
        header_frame.pack(pady=10)

        title_label = tk.Label(header_frame, text="INTERACTIVE CPU SCHEDULING SIMULATOR",
                               font=("Arial", 18, "bold"), bg="#0f1524", fg="#00e6ff")
        title_label.pack()

        subtitle_label = tk.Label(header_frame, text="FCFS • SJF • Priority • Round Robin • Enhanced Features",
                                  font=("Arial", 12), bg="#0f1524", fg="#8a8d93")
        subtitle_label.pack(pady=5)

        # Music controls
        music_frame = ttk.Frame(header_frame)
        music_frame.pack(pady=5)

        self.music_btn = tk.Button(music_frame, text="Play Music", command=self.toggle_music,
                                   bg="#1a2337", fg="#00e6ff", font=("Arial", 9, "bold"),
                                   relief="flat", bd=0, padx=10, pady=3)
        self.music_btn.pack(side=tk.LEFT, padx=5)
        self.create_glow_effect(self.music_btn, "#00e6ff")

        load_music_btn = tk.Button(music_frame, text="Load Music", command=self.load_music,
                                   bg="#1a2337", fg="#00e6ff", font=("Arial", 9, "bold"),
                                   relief="flat", bd=0, padx=10, pady=3)
        load_music_btn.pack(side=tk.LEFT, padx=5)
        self.create_glow_effect(load_music_btn, "#00e6ff")

        # Sound effects button
        sound_btn = tk.Button(music_frame, text="Toggle Sounds", command=self.toggle_sounds,
                              bg="#1a2337", fg="#00e6ff", font=("Arial", 9, "bold"),
                              relief="flat", bd=0, padx=10, pady=3)
        sound_btn.pack(side=tk.LEFT, padx=5)
        self.create_glow_effect(sound_btn, "#00e6ff")
        self.sounds_enabled = True

        # Input frame
        input_frame = ttk.Frame(self.scheduler_frame)
        input_frame.pack(pady=15)

        ttk.Label(input_frame, text="Process ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5)
        self.pid_entry = ttk.Entry(input_frame, width=12, font=("Arial", 10))
        self.pid_entry.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Arrival Time:", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5)
        self.arrival_entry = ttk.Entry(input_frame, width=12, font=("Arial", 10))
        self.arrival_entry.grid(row=0, column=3, padx=5)

        ttk.Label(input_frame, text="Burst Time:", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=5)
        self.burst_entry = ttk.Entry(input_frame, width=12, font=("Arial", 10))
        self.burst_entry.grid(row=0, column=5, padx=5)

        ttk.Label(input_frame, text="Priority:", font=("Arial", 10, "bold")).grid(row=0, column=6, padx=5)
        self.priority_entry = ttk.Entry(input_frame, width=12, font=("Arial", 10))
        self.priority_entry.grid(row=0, column=7, padx=5)
        self.priority_entry.insert(0, "1")

        # Add Process button with futuristic style
        add_btn = tk.Button(input_frame, text="Add Process", command=self.add_process,
                            bg="#1a2337", fg="#00e6ff", font=("Arial", 10, "bold"),
                            relief="flat", bd=0, padx=15, pady=5,
                            activebackground="#243b55", activeforeground="#00e6ff")
        add_btn.grid(row=0, column=8, padx=10)
        self.create_glow_effect(add_btn, "#00e6ff")

        # Algorithm selection
        algo_frame = ttk.Frame(self.scheduler_frame)
        algo_frame.pack(pady=15)

        self.algo = tk.StringVar(value="FCFS")

        algo_style = {"font": ("Arial", 10, "bold"), "bg": "#0f1524", "fg": "#00e6ff",
                      "selectcolor": "#1a2337", "activebackground": "#0f1524"}

        tk.Radiobutton(algo_frame, text="FCFS", variable=self.algo, value="FCFS", **algo_style).pack(side=tk.LEFT,
                                                                                                     padx=15)
        tk.Radiobutton(algo_frame, text="SJF Non-Preemptive", variable=self.algo, value="SJFNP", **algo_style).pack(
            side=tk.LEFT, padx=15)
        tk.Radiobutton(algo_frame, text="SJF Preemptive", variable=self.algo, value="SJFP", **algo_style).pack(
            side=tk.LEFT, padx=15)
        tk.Radiobutton(algo_frame, text="Priority Non-Preemptive", variable=self.algo, value="PriorityNP",
                       **algo_style).pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(algo_frame, text="Priority Preemptive", variable=self.algo, value="PriorityP",
                       **algo_style).pack(side=tk.LEFT, padx=15)

        rr_frame = ttk.Frame(algo_frame)
        rr_frame.pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(rr_frame, text="Round Robin", variable=self.algo, value="RR", **algo_style).pack(side=tk.LEFT)
        ttk.Label(rr_frame, text="Quantum:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        quantum_entry = ttk.Entry(rr_frame, textvariable=self.time_quantum, width=3, font=("Arial", 9))
        quantum_entry.pack(side=tk.LEFT)

        # Enhanced algorithm options
        enhanced_frame = ttk.Frame(algo_frame)
        enhanced_frame.pack(side=tk.LEFT, padx=15)

        tk.Radiobutton(enhanced_frame, text="Enhanced Priority", variable=self.algo, value="EnhancedPriority",
                       **algo_style).pack(side=tk.LEFT)
        tk.Radiobutton(enhanced_frame, text="Enhanced RR", variable=self.algo, value="EnhancedRR",
                       **algo_style).pack(side=tk.LEFT)

        # Control buttons
        control_frame = ttk.Frame(self.scheduler_frame)
        control_frame.pack(pady=10)

        simulate_btn = tk.Button(control_frame, text="Simulate", command=self.simulate,
                                 bg="#00c853", fg="white", font=("Arial", 10, "bold"),
                                 relief="flat", bd=0, padx=20, pady=6,
                                 activebackground="#00e676", activeforeground="white")
        simulate_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(simulate_btn, "#00c853")

        clear_btn = tk.Button(control_frame, text="Clear All", command=self.clear_all,
                              bg="#ff3d00", fg="white", font=("Arial", 10, "bold"),
                              relief="flat", bd=0, padx=20, pady=6,
                              activebackground="#ff6d40", activeforeground="white")
        clear_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(clear_btn, "#ff3d00")

        generate_btn = tk.Button(control_frame, text="Generate Random", command=self.generate_random_processes,
                                 bg="#aa00ff", fg="white", font=("Arial", 10, "bold"),
                                 relief="flat", bd=0, padx=20, pady=6,
                                 activebackground="#d500f9", activeforeground="white")
        generate_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(generate_btn, "#aa00ff")

        # Creating a Table in our GUI/Program
        table_frame = ttk.Frame(self.scheduler_frame)
        table_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        # Add scrollbar to table
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Process ID", "Arrival Time", "Burst Time", "Priority", "Completion Time", "Waiting Time",
                     "Turnaround Time", "Response Time"),
            show='headings',
            height=8,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Configure column headings
        columns = ["Process ID", "Arrival Time", "Burst Time", "Priority", "Completion Time", "Waiting Time",
                   "Turnaround Time", "Response Time"]
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status = tk.StringVar()
        status_label = ttk.Label(self.scheduler_frame, textvariable=self.status, font=("Arial", 11, "bold"),
                                 foreground="#00e6ff")
        status_label.pack(pady=5)

        # Label for Gantt Chart
        self.gantt_label = tk.Label(
            self.scheduler_frame,
            text="INTERACTIVE GANTT CHART VISUALIZATION",
            font=("Arial", 14, "bold"),
            anchor="center",
            bg="#0f1524",
            fg="#00e6ff"
        )
        self.gantt_label.pack(pady=10)

        # Interactive Gantt Chart using matplotlib
        gantt_frame = ttk.Frame(self.scheduler_frame)
        gantt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create matplotlib figure for Gantt chart
        self.gantt_fig = Figure(figsize=(10, 4), dpi=100, facecolor='#1a2337')
        self.gantt_ax = self.gantt_fig.add_subplot(111)
        self.gantt_ax.set_facecolor('#1a2337')
        self.gantt_ax.tick_params(colors='#00e6ff')
        for spine in self.gantt_ax.spines.values():
            spine.set_color('#00e6ff')

        # Create canvas for matplotlib figure
        self.gantt_canvas = FigureCanvasTkAgg(self.gantt_fig, gantt_frame)
        self.gantt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar for interactive features
        toolbar = NavigationToolbar2Tk(self.gantt_canvas, gantt_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_system_monitor_ui(self):
        # System Monitor UI
        title_label = tk.Label(self.system_monitor_frame, text="SYSTEM PERFORMANCE MONITOR",
                               font=("Arial", 18, "bold"), bg="#0f1524", fg="#00e6ff")
        title_label.pack(pady=10)

        # System info frame
        sys_info_frame = ttk.Frame(self.system_monitor_frame)
        sys_info_frame.pack(fill=tk.X, padx=20, pady=10)

        # System information
        self.sys_info_text = tk.Text(sys_info_frame, height=8, width=80, bg="#1a2337", fg="#00e6ff",
                                     font=("Arial", 10), relief="flat")
        self.sys_info_text.pack(fill=tk.BOTH, expand=True)

        # CPU and Memory usage
        usage_frame = ttk.Frame(self.system_monitor_frame)
        usage_frame.pack(fill=tk.X, padx=20, pady=10)

        # CPU usage
        cpu_frame = ttk.Frame(usage_frame)
        cpu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(cpu_frame, text="CPU USAGE", font=("Arial", 12, "bold")).pack(pady=5)
        self.cpu_usage = tk.StringVar(value="0%")
        ttk.Label(cpu_frame, textvariable=self.cpu_usage, font=("Arial", 24, "bold")).pack(pady=5)
        self.cpu_bar = ttk.Progressbar(cpu_frame, orient="horizontal", length=200, mode="determinate")
        self.cpu_bar.pack(pady=5, fill=tk.X)

        # Memory usage
        mem_frame = ttk.Frame(usage_frame)
        mem_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(mem_frame, text="MEMORY USAGE", font=("Arial", 12, "bold")).pack(pady=5)
        self.mem_usage = tk.StringVar(value="0%")
        ttk.Label(mem_frame, textvariable=self.mem_usage, font=("Arial", 24, "bold")).pack(pady=5)
        self.mem_bar = ttk.Progressbar(mem_frame, orient="horizontal", length=200, mode="determinate")
        self.mem_bar.pack(pady=5, fill=tk.X)

        # Disk usage
        disk_frame = ttk.Frame(usage_frame)
        disk_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(disk_frame, text="DISK USAGE", font=("Arial", 12, "bold")).pack(pady=5)
        self.disk_usage = tk.StringVar(value="0%")
        ttk.Label(disk_frame, textvariable=self.disk_usage, font=("Arial", 24, "bold")).pack(pady=5)
        self.disk_bar = ttk.Progressbar(disk_frame, orient="horizontal", length=200, mode="determinate")
        self.disk_bar.pack(pady=5, fill=tk.X)

        # Network stats
        net_frame = ttk.Frame(self.system_monitor_frame)
        net_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(net_frame, text="NETWORK STATISTICS", font=("Arial", 12, "bold")).pack(pady=5)

        net_stats_frame = ttk.Frame(net_frame)
        net_stats_frame.pack(fill=tk.X)

        ttk.Label(net_stats_frame, text="Bytes Sent:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.bytes_sent = tk.StringVar(value="0")
        ttk.Label(net_stats_frame, textvariable=self.bytes_sent, font=("Arial", 10)).grid(row=0, column=1, sticky=tk.W,
                                                                                          padx=5)

        ttk.Label(net_stats_frame, text="Bytes Received:", font=("Arial", 10)).grid(row=0, column=2, sticky=tk.W,
                                                                                    padx=5)
        self.bytes_recv = tk.StringVar(value="0")
        ttk.Label(net_stats_frame, textvariable=self.bytes_recv, font=("Arial", 10)).grid(row=0, column=3, sticky=tk.W,
                                                                                          padx=5)

        ttk.Label(net_stats_frame, text="Packets Sent:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.packets_sent = tk.StringVar(value="0")
        ttk.Label(net_stats_frame, textvariable=self.packets_sent, font=("Arial", 10)).grid(row=1, column=1,
                                                                                            sticky=tk.W, padx=5)

        ttk.Label(net_stats_frame, text="Packets Received:", font=("Arial", 10)).grid(row=1, column=2, sticky=tk.W,
                                                                                      padx=5)
        self.packets_recv = tk.StringVar(value="0")
        ttk.Label(net_stats_frame, textvariable=self.packets_recv, font=("Arial", 10)).grid(row=1, column=3,
                                                                                            sticky=tk.W, padx=5)

    def create_process_manager_ui(self):
        # Process Manager UI
        title_label = tk.Label(self.process_manager_frame, text="SYSTEM PROCESS MANAGER",
                               font=("Arial", 18, "bold"), bg="#0f1524", fg="#00e6ff")
        title_label.pack(pady=10)

        # Refresh button
        refresh_btn = tk.Button(self.process_manager_frame, text="Refresh Processes", command=self.refresh_process_list,
                                bg="#1a2337", fg="#00e6ff", font=("Arial", 10, "bold"),
                                relief="flat", bd=0, padx=15, pady=5,
                                activebackground="#243b55", activeforeground="#00e6ff")
        refresh_btn.pack(pady=10)
        self.create_glow_effect(refresh_btn, "#00e6ff")

        # Process table
        table_frame = ttk.Frame(self.process_manager_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Add scrollbar to table
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.process_tree = ttk.Treeview(
            table_frame,
            columns=("PID", "Name", "Status", "CPU %", "Memory %", "Threads"),
            show='headings',
            height=15,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.process_tree.yview)

        # Configure column headings
        columns = ["PID", "Name", "Status", "CPU %", "Memory %", "Threads"]
        for col in columns:
            self.process_tree.heading(col, text=col, anchor=tk.CENTER)
            self.process_tree.column(col, anchor=tk.CENTER, width=100)

        self.process_tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = ttk.Frame(self.process_manager_frame)
        action_frame.pack(pady=10)

        kill_btn = tk.Button(action_frame, text="Kill Process", command=self.kill_selected_process,
                             bg="#ff3d00", fg="white", font=("Arial", 10, "bold"),
                             relief="flat", bd=0, padx=15, pady=5,
                             activebackground="#ff6d40", activeforeground="white")
        kill_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(kill_btn, "#ff3d00")

        suspend_btn = tk.Button(action_frame, text="Suspend Process", command=self.suspend_selected_process,
                                bg="#ffab00", fg="white", font=("Arial", 10, "bold"),
                                relief="flat", bd=0, padx=15, pady=5,
                                activebackground="#ffd600", activeforeground="white")
        suspend_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(suspend_btn, "#ffab00")

        resume_btn = tk.Button(action_frame, text="Resume Process", command=self.resume_selected_process,
                               bg="#00c853", fg="white", font=("Arial", 10, "bold"),
                               relief="flat", bd=0, padx=15, pady=5,
                               activebackground="#00e676", activeforeground="white")
        resume_btn.pack(side=tk.LEFT, padx=10)
        self.create_glow_effect(resume_btn, "#00c853")

    def create_analysis_ui(self):
        # Performance Analysis UI
        title_label = tk.Label(self.analysis_frame, text="ALGORITHM PERFORMANCE ANALYSIS",
                               font=("Arial", 18, "bold"), bg="#0f1524", fg="#00e6ff")
        title_label.pack(pady=10)

        # Frame for algorithm comparison
        compare_frame = ttk.Frame(self.analysis_frame)
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create matplotlib figure for algorithm comparison
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor='#1a2337')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1a2337')
        self.ax.tick_params(colors='#00e6ff')
        for spine in self.ax.spines.values():
            spine.set_color('#00e6ff')

        # Create canvas for matplotlib figure
        self.canvas_analysis = FigureCanvasTkAgg(self.fig, compare_frame)
        self.canvas_analysis.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar for interactive features
        toolbar = NavigationToolbar2Tk(self.canvas_analysis, compare_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Button to update analysis
        update_btn = tk.Button(self.analysis_frame, text="Update Analysis", command=self.update_analysis,
                               bg="#1a2337", fg="#00e6ff", font=("Arial", 10, "bold"),
                               relief="flat", bd=0, padx=15, pady=5,
                               activebackground="#243b55", activeforeground="#00e6ff")
        update_btn.pack(pady=10)
        self.create_glow_effect(update_btn, "#00e6ff")

    def toggle_music(self):
        """Toggle background music on/off"""
        if self.music_playing:
            pygame.mixer.music.stop()
            self.music_btn.config(text="Play Music")
            self.music_playing = False
        else:
            if self.current_music:
                pygame.mixer.music.load(self.current_music)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                self.music_btn.config(text="Stop Music")
                self.music_playing = True
            else:
                messagebox.showinfo("Info", "Please load a music file first")

    def toggle_sounds(self):
        """Toggle sound effects on/off"""
        self.sounds_enabled = not self.sounds_enabled
        if self.sounds_enabled:
            self.play_sound("medium")
            messagebox.showinfo("Sound Effects", "Sound effects enabled")
        else:
            messagebox.showinfo("Sound Effects", "Sound effects disabled")

    def load_music(self):
        """Load a music file for background music"""
        file_path = filedialog.askopenfilename(
            title="Select Music File",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")]
        )
        if file_path:
            self.current_music = file_path
            if self.music_playing:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play(-1)

    def update_analysis(self):
        """Update the algorithm performance analysis chart"""
        if not self.algorithm_stats:
            messagebox.showinfo("Info", "Run simulations first to generate performance data")
            return

        self.ax.clear()

        # Prepare data for visualization
        algorithms = list(self.algorithm_stats.keys())
        avg_waiting_times = [self.algorithm_stats[algo]['avg_waiting_time'] for algo in algorithms]
        avg_turnaround_times = [self.algorithm_stats[algo]['avg_turnaround_time'] for algo in algorithms]
        avg_response_times = [self.algorithm_stats[algo]['avg_response_time'] for algo in algorithms]

        x = np.arange(len(algorithms))
        width = 0.25

        # Create bars for each metric
        bars1 = self.ax.bar(x - width, avg_waiting_times, width, label='Avg Waiting Time', color='#00e6ff')
        bars2 = self.ax.bar(x, avg_turnaround_times, width, label='Avg Turnaround Time', color='#00c853')
        bars3 = self.ax.bar(x + width, avg_response_times, width, label='Avg Response Time', color='#aa00ff')

        # Customize the chart
        self.ax.set_xlabel('Algorithms', color='#00e6ff')
        self.ax.set_ylabel('Time Units', color='#00e6ff')
        self.ax.set_title('Algorithm Performance Comparison', color='#00e6ff')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(algorithms, color='#00e6ff')
        self.ax.legend(facecolor='#1a2337', edgecolor='#1a2337', labelcolor='#00e6ff')

        # Add value labels on top of bars
        for i, v in enumerate(avg_waiting_times):
            self.ax.text(i - width, v + 0.1, f'{v:.2f}', ha='center', color='#00e6ff')
        for i, v in enumerate(avg_turnaround_times):
            self.ax.text(i, v + 0.1, f'{v:.2f}', ha='center', color='#00c853')
        for i, v in enumerate(avg_response_times):
            self.ax.text(i + width, v + 0.1, f'{v:.2f}', ha='center', color='#aa00ff')

        # Play sound if values are high
        if self.sounds_enabled:
            max_waiting = max(avg_waiting_times)
            if max_waiting > 15:  # Threshold for high waiting time
                self.play_sound("high")
            elif max_waiting > 10:
                self.play_sound("medium")

        # Update the canvas
        self.canvas_analysis.draw()

    def on_tab_changed(self, event):
        # Get the currently selected tab
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        self.current_tab = current_tab.lower().replace(" ", "_")

        if self.current_tab == "system_monitor":
            self.update_system_info()
        elif self.current_tab == "process_manager":
            self.refresh_process_list()
        elif self.current_tab == "performance_analysis":
            self.update_analysis()

    def update_system_stats(self):
        if self.current_tab == "system_monitor":
            # Update CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(f"{cpu_percent}%")
            self.cpu_bar["value"] = cpu_percent

            # Update memory usage
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            self.mem_usage.set(f"{mem_percent}%")
            self.mem_bar["value"] = mem_percent

            # Update disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.disk_usage.set(f"{disk_percent}%")
            self.disk_bar["value"] = disk_percent

            # Update network stats
            net_io = psutil.net_io_counters()
            self.bytes_sent.set(f"{net_io.bytes_sent // 1024} KB")
            self.bytes_recv.set(f"{net_io.bytes_recv // 1024} KB")
            self.packets_sent.set(str(net_io.packets_sent))
            self.packets_recv.set(str(net_io.packets_recv))

            # Update system info
            self.update_system_info()

            # Play sound if usage is high
            if self.sounds_enabled:
                if cpu_percent > 80:
                    self.play_sound("high")
                elif cpu_percent > 60:
                    self.play_sound("medium")

        # Schedule the next update
        self.after(1000, self.update_system_stats)

    def update_system_info(self):
        # Clear previous content
        self.sys_info_text.delete(1.0, tk.END)

        # Get system information
        info = f"System: {platform.system()} {platform.release()}\n"
        info += f"Platform: {platform.platform()}\n"
        info += f"Processor: {platform.processor()}\n"
        info += f"CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical\n"

        # Memory information
        memory = psutil.virtual_memory()
        info += f"Total Memory: {memory.total // (1024 ** 3)} GB\n"
        info += f"Available Memory: {memory.available // (1024 ** 3)} GB\n"

        # Disk information
        disk = psutil.disk_usage('/')
        info += f"Total Disk Space: {disk.total // (1024 ** 3)} GB\n"
        info += f"Free Disk Space: {disk.free // (1024 ** 3)} GB\n"

        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        info += f"System Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Insert the information into the text widget
        self.sys_info_text.insert(tk.END, info)

    def refresh_process_list(self):
        # Clear the treeview
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        # Get all processes
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'num_threads']):
            try:
                self.process_tree.insert('', 'end', values=(
                    proc.info['pid'],
                    proc.info['name'],
                    proc.info['status'],
                    f"{proc.info['cpu_percent']:.1f}" if proc.info['cpu_percent'] else "0.0",
                    f"{proc.info['memory_percent']:.1f}" if proc.info['memory_percent'] else "0.0",
                    proc.info['num_threads']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def kill_selected_process(self):
        selected = self.process_tree.selection()
        if selected:
            pid = self.process_tree.item(selected[0])['values'][0]
            try:
                process = psutil.Process(pid)
                process.terminate()
                if self.sounds_enabled:
                    self.play_sound("complete")
                messagebox.showinfo("Success", f"Process {pid} terminated successfully")
                self.refresh_process_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to terminate process: {str(e)}")

    def suspend_selected_process(self):
        selected = self.process_tree.selection()
        if selected:
            pid = self.process_tree.item(selected[0])['values'][0]
            try:
                process = psutil.Process(pid)
                process.suspend()
                if self.sounds_enabled:
                    self.play_sound("medium")
                messagebox.showinfo("Success", f"Process {pid} suspended successfully")
                self.refresh_process_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to suspend process: {str(e)}")

    def resume_selected_process(self):
        selected = self.process_tree.selection()
        if selected:
            pid = self.process_tree.item(selected[0])['values'][0]
            try:
                process = psutil.Process(pid)
                process.resume()
                if self.sounds_enabled:
                    self.play_sound("medium")
                messagebox.showinfo("Success", f"Process {pid} resumed successfully")
                self.refresh_process_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to resume process: {str(e)}")

    def create_glow_effect(self, widget, color):
        def on_enter(e):
            widget.config(highlightbackground=color, highlightcolor=color, highlightthickness=2)

        def on_leave(e):
            widget.config(highlightthickness=0)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def add_process(self):
        pid = self.pid_entry.get().strip()
        arrival = self.arrival_entry.get().strip()
        burst = self.burst_entry.get().strip()
        priority = self.priority_entry.get().strip()

        # Check if PID is provided
        if not pid:
            messagebox.showerror("Input Error", "Please enter a Process ID.")
            return

        # Validate arrival time
        try:
            arrival_val = float(arrival)
            if arrival_val < 0:
                messagebox.showerror("Input Error", "Arrival Time cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Arrival Time must be a number.")
            return

        # Validate burst time
        try:
            burst_val = float(burst)
            if burst_val <= 0:
                messagebox.showerror("Input Error", "Burst Time must be positive.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Burst Time must be a number.")
            return

        # Validate priority
        try:
            priority_val = int(priority)
            if priority_val < 1:
                messagebox.showerror("Input Error", "Priority must be at least 1.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Priority must be an integer.")
            return

        # Convert to integers if they're whole numbers
        if arrival_val.is_integer():
            arrival_val = int(arrival_val)
        if burst_val.is_integer():
            burst_val = int(burst_val)

        p = Process(pid, arrival_val, burst_val, priority_val)
        self.processes.append(p)
        self.tree.insert('', 'end', values=(pid, arrival_val, burst_val, priority_val, '', '', '', ''))
        self.colors[pid] = f'#{random.randint(0, 100):02x}{random.randint(100, 200):02x}{random.randint(200, 255):02x}'
        self.pid_entry.delete(0, tk.END)
        self.arrival_entry.delete(0, tk.END)
        self.burst_entry.delete(0, tk.END)

        if self.sounds_enabled:
            self.play_sound("medium")

    def generate_random_processes(self):
        num_processes = random.randint(3, 8)
        for i in range(num_processes):
            pid = f"P{i + 1}"
            arrival = random.randint(0, 10)
            burst = random.randint(1, 15)
            priority = random.randint(1, 5)

            p = Process(pid, arrival, burst, priority)
            self.processes.append(p)
            self.tree.insert('', 'end', values=(pid, arrival, burst, priority, '', '', '', ''))
            self.colors[
                pid] = f'#{random.randint(0, 100):02x}{random.randint(100, 200):02x}{random.randint(200, 255):02x}'

        if self.sounds_enabled:
            self.play_sound("complete")

    def clear_all(self):
        self.processes = []
        self.colors = {}
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.status.set("")
        self.gantt_ax.clear()
        self.gantt_canvas.draw()

        if self.sounds_enabled:
            self.play_sound("low")

    def simulate(self):
        if not self.processes:
            messagebox.showerror("No Processes", "Please add at least one process.")
            return
        self.status.set("Simulating...")
        if self.sounds_enabled:
            self.play_sound("medium")
        self.after(100, lambda: threading.Thread(target=self._run_simulation).start())

    def _run_simulation(self):
        algo = self.algo.get()
        procs = [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in self.processes]

        if algo == "FCFS":
            procs = self.fcfs(procs)
        elif algo == "SJFNP":
            procs = self.sjf_non_preemptive(procs)
        elif algo == "SJFP":
            procs = self.sjf_preemptive(procs)
        elif algo == "PriorityNP":
            procs = self.priority_non_preemptive(procs)
        elif algo == "PriorityP":
            procs = self.priority_preemptive(procs)
        elif algo == "RR":
            quantum = self.time_quantum.get()
            procs = self.round_robin(procs, quantum)
        elif algo == "EnhancedPriority":
            procs = self.enhanced_priority(procs)
        elif algo == "EnhancedRR":
            quantum = self.time_quantum.get()
            procs = self.enhanced_round_robin(procs, quantum)
        else:
            return

        # Store algorithm performance metrics
        self.store_algorithm_stats(algo, procs)

        self.after(0, lambda: self.display_result(procs))

    def store_algorithm_stats(self, algo_name, procs):
        """Store performance metrics for algorithm comparison"""
        total_wt = sum(p.waiting_time for p in procs)
        total_tat = sum(p.turnaround_time for p in procs)
        total_rt = sum(p.response_time for p in procs)
        n = len(procs)

        self.algorithm_stats[algo_name] = {
            'avg_waiting_time': total_wt / n,
            'avg_turnaround_time': total_tat / n,
            'avg_response_time': total_rt / n,
            'process_count': n
        }

    def fcfs(self, procs):
        procs.sort(key=lambda x: (x.arrival_time, x.pid))
        current_time = 0
        for p in procs:
            if current_time < p.arrival_time:
                current_time = p.arrival_time
            p.start_time = current_time
            p.waiting_time = current_time - p.arrival_time
            p.completion_time = current_time + p.burst_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.response_time = p.start_time - p.arrival_time  # Response time is same as waiting time in FCFS
            p.execution_log.append((p.start_time, p.completion_time))
            current_time += p.burst_time
        return procs

    def sjf_non_preemptive(self, procs):
        procs.sort(key=lambda x: (x.arrival_time, x.burst_time, x.pid))
        ready_queue, completed = [], []
        current_time, idx = 0, 0
        while len(completed) < len(procs):
            while idx < len(procs) and procs[idx].arrival_time <= current_time:
                ready_queue.append(procs[idx])
                idx += 1
            if ready_queue:
                ready_queue.sort(key=lambda x: (x.burst_time, x.arrival_time))
                p = ready_queue.pop(0)
                if current_time < p.arrival_time:
                    current_time = p.arrival_time
                p.start_time = current_time
                p.waiting_time = current_time - p.arrival_time
                p.completion_time = current_time + p.burst_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.response_time = p.start_time - p.arrival_time
                p.execution_log.append((p.start_time, p.completion_time))
                current_time += p.burst_time
                completed.append(p)
            else:
                current_time += 1
        return completed

    def sjf_preemptive(self, procs):
        current_time, completed = 0, []
        ready_queue = []
        n = len(procs)
        while len(completed) < n:
            for p in procs:
                if p.arrival_time == current_time and p not in ready_queue and p not in completed:
                    ready_queue.append(p)
            if ready_queue:
                ready_queue.sort(key=lambda x: (x.remaining_time, x.arrival_time))
                p = ready_queue[0]
                if p.start_time is None:
                    p.start_time = current_time
                    p.response_time = p.start_time - p.arrival_time
                start = current_time
                current_time += 1
                p.remaining_time -= 1
                end = current_time
                p.execution_log.append((start, end))
                if p.remaining_time == 0:
                    p.completion_time = current_time
                    p.turnaround_time = p.completion_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    completed.append(p)
                    ready_queue.remove(p)
            else:
                current_time += 1
        return procs

    def priority_non_preemptive(self, procs):
        procs.sort(key=lambda x: (x.arrival_time, x.priority, x.pid))
        ready_queue, completed = [], []
        current_time, idx = 0, 0
        while len(completed) < len(procs):
            while idx < len(procs) and procs[idx].arrival_time <= current_time:
                ready_queue.append(procs[idx])
                idx += 1
            if ready_queue:
                ready_queue.sort(key=lambda x: (x.priority, x.arrival_time))
                p = ready_queue.pop(0)
                if current_time < p.arrival_time:
                    current_time = p.arrival_time
                p.start_time = current_time
                p.waiting_time = current_time - p.arrival_time
                p.completion_time = current_time + p.burst_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.response_time = p.start_time - p.arrival_time
                p.execution_log.append((p.start_time, p.completion_time))
                current_time += p.burst_time
                completed.append(p)
            else:
                current_time += 1
        return completed

    def priority_preemptive(self, procs):
        current_time, completed = 0, []
        ready_queue = []
        n = len(procs)
        while len(completed) < n:
            for p in procs:
                if p.arrival_time == current_time and p not in ready_queue and p not in completed:
                    ready_queue.append(p)
            if ready_queue:
                ready_queue.sort(key=lambda x: (x.priority, x.arrival_time))
                p = ready_queue[0]
                if p.start_time is None:
                    p.start_time = current_time
                    p.response_time = p.start_time - p.arrival_time
                start = current_time
                current_time += 1
                p.remaining_time -= 1
                end = current_time
                p.execution_log.append((start, end))
                if p.remaining_time == 0:
                    p.completion_time = current_time
                    p.turnaround_time = p.completion_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    completed.append(p)
                    ready_queue.remove(p)
            else:
                current_time += 1
        return procs

    def round_robin(self, procs, quantum):
        procs.sort(key=lambda x: x.arrival_time)
        ready_queue = []
        current_time = 0
        completed = []
        idx = 0
        n = len(procs)

        while len(completed) < n:
            # Add arriving processes to ready queue
            while idx < n and procs[idx].arrival_time <= current_time:
                ready_queue.append(procs[idx])
                idx += 1

            if ready_queue:
                p = ready_queue.pop(0)
                if p.start_time is None:
                    p.start_time = current_time
                    p.response_time = p.start_time - p.arrival_time

                # Execute for quantum or until completion
                exec_time = min(quantum, p.remaining_time)
                start = current_time
                current_time += exec_time
                p.remaining_time -= exec_time
                end = current_time
                p.execution_log.append((start, end))

                # Add arriving processes during execution
                while idx < n and procs[idx].arrival_time <= current_time:
                    ready_queue.append(procs[idx])
                    idx += 1

                # If not completed, add back to ready queue
                if p.remaining_time > 0:
                    ready_queue.append(p)
                else:
                    p.completion_time = current_time
                    p.turnaround_time = p.completion_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    completed.append(p)
            else:
                current_time += 1

        return completed

    def enhanced_priority(self, procs):
        """Enhanced Priority Scheduling with aging to prevent starvation"""
        procs.sort(key=lambda x: x.arrival_time)
        ready_queue = []
        current_time = 0
        completed = []
        idx = 0
        n = len(procs)

        # Aging factor - priority increases by 1 every 5 time units
        aging_interval = 5
        last_aging_time = 0

        while len(completed) < n:
            # Add arriving processes to ready queue
            while idx < n and procs[idx].arrival_time <= current_time:
                ready_queue.append(procs[idx])
                idx += 1

            # Apply aging to prevent starvation
            if current_time - last_aging_time >= aging_interval:
                for p in ready_queue:
                    # Increase priority (lower number = higher priority)
                    if p.priority > 1:
                        p.priority -= 1
                last_aging_time = current_time

            if ready_queue:
                # Sort by priority (lower number = higher priority)
                ready_queue.sort(key=lambda x: (x.priority, x.arrival_time))
                p = ready_queue[0]
                if p.start_time is None:
                    p.start_time = current_time
                    p.response_time = p.start_time - p.arrival_time

                # Execute for one time unit
                start = current_time
                current_time += 1
                p.remaining_time -= 1
                end = current_time
                p.execution_log.append((start, end))

                # Add arriving processes during execution
                while idx < n and procs[idx].arrival_time <= current_time:
                    ready_queue.append(procs[idx])
                    idx += 1

                # If completed, remove from ready queue
                if p.remaining_time == 0:
                    p.completion_time = current_time
                    p.turnaround_time = p.completion_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    completed.append(p)
                    ready_queue.remove(p)
                else:
                    # Put the process back in the ready queue
                    ready_queue.pop(0)
                    ready_queue.append(p)
            else:
                current_time += 1

        return completed

    def enhanced_round_robin(self, procs, quantum):
        """Enhanced Round Robin with dynamic time quantum"""
        procs.sort(key=lambda x: x.arrival_time)
        ready_queue = []
        current_time = 0
        completed = []
        idx = 0
        n = len(procs)

        # Track burst times for dynamic quantum calculation
        burst_times = [p.burst_time for p in procs]
        avg_burst = sum(burst_times) / n if n > 0 else quantum
        dynamic_quantum = max(1, int(avg_burst * 0.8))  # 80% of average burst time

        while len(completed) < n:
            # Add arriving processes to ready queue
            while idx < n and procs[idx].arrival_time <= current_time:
                ready_queue.append(procs[idx])
                idx += 1

            if ready_queue:
                p = ready_queue.pop(0)
                if p.start_time is None:
                    p.start_time = current_time
                    p.response_time = p.start_time - p.arrival_time

                # Use dynamic quantum for processes with short remaining time
                if p.remaining_time <= dynamic_quantum:
                    exec_time = p.remaining_time
                else:
                    exec_time = dynamic_quantum

                start = current_time
                current_time += exec_time
                p.remaining_time -= exec_time
                end = current_time
                p.execution_log.append((start, end))

                # Add arriving processes during execution
                while idx < n and procs[idx].arrival_time <= current_time:
                    ready_queue.append(procs[idx])
                    idx += 1

                # If not completed, add back to ready queue
                if p.remaining_time > 0:
                    ready_queue.append(p)
                else:
                    p.completion_time = current_time
                    p.turnaround_time = p.completion_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    completed.append(p)
            else:
                current_time += 1

        return completed

    def display_result(self, procs):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_wt = total_tat = total_rt = 0
        for p in procs:
            self.tree.insert('', 'end',
                             values=(p.pid, p.arrival_time, p.burst_time, p.priority,
                                     p.completion_time, p.waiting_time, p.turnaround_time, p.response_time))
            total_wt += p.waiting_time
            total_tat += p.turnaround_time
            total_rt += p.response_time
        avg_wt = total_wt / len(procs)
        avg_tat = total_tat / len(procs)
        avg_rt = total_rt / len(procs)
        self.status.set(
            f"Avg Waiting Time: {avg_wt:.2f}  ||  Avg Turnaround Time: {avg_tat:.2f}  ||  Avg Response Time: {avg_rt:.2f}")

        # Update Gantt chart with matplotlib
        self.update_gantt_chart(procs)

        if self.sounds_enabled:
            self.play_sound("complete")

    def update_gantt_chart(self, procs):
        """Update the Gantt chart with matplotlib"""
        self.gantt_ax.clear()

        # Set up the chart
        self.gantt_ax.set_title('Gantt Chart', color='#00e6ff')
        self.gantt_ax.set_xlabel('Time', color='#00e6ff')
        self.gantt_ax.set_ylabel('Processes', color='#00e6ff')
        self.gantt_ax.set_facecolor('#1a2337')
        self.gantt_ax.tick_params(colors='#00e6ff')
        for spine in self.gantt_ax.spines.values():
            spine.set_color('#00e6ff')

        # Get the maximum time for scaling
        max_time = max(p.completion_time for p in procs) if procs else 1

        # Create bars for each process execution
        y_pos = 0
        y_ticks = []
        y_labels = []

        for p in procs:
            for start, end in p.execution_log:
                color = self.colors.get(p.pid, "#00e6ff")
                self.gantt_ax.barh(y_pos, end - start, left=start, height=0.5,
                                   color=color, edgecolor='white', alpha=0.8)

                # Add process ID label in the middle of the bar
                mid_point = start + (end - start) / 2
                self.gantt_ax.text(mid_point, y_pos, p.pid,
                                   ha='center', va='center', color='black', fontweight='bold')

            y_ticks.append(y_pos)
            y_labels.append(p.pid)
            y_pos += 1

        # Set y-axis labels
        self.gantt_ax.set_yticks(y_ticks)
        self.gantt_ax.set_yticklabels(y_labels)

        # Set x-axis limits and grid
        self.gantt_ax.set_xlim(0, max_time * 1.1)
        self.gantt_ax.grid(True, color='#243b55', linestyle='--', linewidth=0.5)

        # Add interactive features
        self.gantt_fig.tight_layout()
        self.gantt_canvas.draw()

        # Start animation if there are processes
        if procs:
            self.animate_gantt_chart(procs)

    def animate_gantt_chart(self, procs):
        """Animate the Gantt chart to show process execution over time"""
        # Stop any existing animation
        if self.animation:
            self.animation.event_source.stop()

        # Find the maximum time
        max_time = max(p.completion_time for p in procs)

        # Create a time indicator line
        time_line = self.gantt_ax.axvline(x=0, color='red', linewidth=2, linestyle='--')

        # Create a text annotation for the current time
        time_text = self.gantt_ax.text(0.02, 0.95, '', transform=self.gantt_ax.transAxes, color='red')

        # Get all the bars for highlighting
        bars = []
        for p in procs:
            for start, end in p.execution_log:
                bars.append((start, end, p.pid))

        def update_animation(frame):
            # Update the time line
            time_line.set_xdata([frame, frame])

            # Update the time text
            time_text.set_text(f'Time: {frame}')

            # Highlight the current executing process
            current_process = None
            for start, end, pid in bars:
                if start <= frame < end:
                    current_process = pid
                    break

            # Change the color of the current process bar
            for i, rect in enumerate(self.gantt_ax.patches):
                bar_start = rect.get_x()
                bar_end = bar_start + rect.get_width()
                if bar_start <= frame < bar_end:
                    rect.set_alpha(1.0)
                    # Play sound for process execution
                    if frame % 5 == 0 and self.sounds_enabled:  # Play sound every 5 time units
                        self.play_sound("medium")
                else:
                    rect.set_alpha(0.6)

            return time_line, time_text

        # Create the animation
        self.animation = FuncAnimation(self.gantt_fig, update_animation,
                                       frames=np.arange(0, max_time + 1, 0.5),
                                       interval=500, blit=True, repeat=True)

        # Update the canvas
        self.gantt_canvas.draw()


if __name__ == "__main__":
    app = SystemUtilitiesDashboard()
    app.mainloop()