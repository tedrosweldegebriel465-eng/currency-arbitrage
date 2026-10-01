#!/usr/bin/env python3
"""
GUI Interface for Currency Arbitrage Detector
Clean ASCII interface without special characters
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import math
from datetime import datetime

class ArbitrageGUI:
    """Graphical user interface for arbitrage detection"""
    
    def __init__(self, detector, graph):
        self.detector = detector
        self.graph = graph
        self.root = tk.Tk()
        self.root.title("Currency Arbitrage Detector")
        self.root.geometry("1200x800")
        self.root.minsize(1080, 720)
        self.palette = {
            "bg": "#f4f7fb",
            "panel": "#ffffff",
            "panel_alt": "#eef4fb",
            "ink": "#18324a",
            "muted": "#61758a",
            "accent": "#0f6cbd",
            "accent_dark": "#0b4f8a",
            "line": "#d7e2ee",
            "success": "#0a7d5a",
            "warning": "#b36912",
        }
        self.root.configure(bg=self.palette["bg"])
        self._configure_styles()
        
        self.setup_ui()

    def _configure_styles(self):
        """Configure a custom ttk style system for the desktop UI."""
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            ".",
            background=self.palette["bg"],
            foreground=self.palette["ink"],
            font=("Segoe UI", 10),
        )
        style.configure("App.TFrame", background=self.palette["bg"])
        style.configure("Card.TFrame", background=self.palette["panel"])
        style.configure(
            "Card.TLabelframe",
            background=self.palette["panel"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.palette["panel"],
            foreground=self.palette["ink"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Heading.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["ink"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Body.TLabel",
            background=self.palette["panel"],
            foreground=self.palette["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Status.TLabel",
            background=self.palette["panel_alt"],
            foreground=self.palette["ink"],
            padding=(10, 8),
            font=("Segoe UI Semibold", 10),
            relief="flat",
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(10, 10),
            borderwidth=0,
            background=self.palette["accent"],
            foreground="#ffffff",
        )
        style.map(
            "Accent.TButton",
            background=[
                ("pressed", self.palette["accent_dark"]),
                ("active", self.palette["accent_dark"]),
            ],
            foreground=[("disabled", "#dce7f3"), ("!disabled", "#ffffff")],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(10, 10),
            borderwidth=1,
            background=self.palette["panel_alt"],
            foreground=self.palette["ink"],
        )
        style.map(
            "Secondary.TButton",
            background=[
                ("pressed", "#dfeaf5"),
                ("active", "#e6eff8"),
            ],
        )
        style.configure(
            "TCombobox",
            padding=6,
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground=self.palette["ink"],
        )
        style.configure(
            "TEntry",
            padding=6,
            fieldbackground="#ffffff",
            foreground=self.palette["ink"],
        )
        style.configure(
            "TNotebook",
            background=self.palette["bg"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            padding=(16, 10),
            background="#e7eef7",
            foreground=self.palette["muted"],
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.palette["panel"]), ("active", "#edf3fa")],
            foreground=[("selected", self.palette["ink"]), ("active", self.palette["ink"])],
        )
        style.configure("TSeparator", background=self.palette["line"])
        
    def setup_ui(self):
        """Setup all UI components"""
        hero = tk.Frame(self.root, bg=self.palette["bg"])
        hero.pack(fill=tk.X, padx=24, pady=(22, 10))

        title = tk.Label(
            hero,
            text="CURRENCY ARBITRAGE DETECTOR",
            font=("Segoe UI Semibold", 30),
            bg=self.palette["bg"],
            fg=self.palette["ink"],
        )
        title.pack()
        
        subtitle = tk.Label(
            hero,
            text="Bellman-Ford Algorithm | Negative Cycle Detection",
            font=("Segoe UI", 12),
            bg=self.palette["bg"],
            fg=self.palette["muted"],
        )
        subtitle.pack(pady=(6, 0))

        description = tk.Label(
            hero,
            text="Analyze exchange-rate graphs, inspect shortest paths, and explore arbitrage cycles in one workspace.",
            font=("Segoe UI", 10),
            bg=self.palette["bg"],
            fg=self.palette["muted"],
        )
        description.pack(pady=(6, 0))
        
        main_frame = ttk.Frame(self.root, style="App.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(4, 24))
        
        left_panel = ttk.Frame(main_frame, width=320, style="Card.TFrame")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        left_panel.pack_propagate(False)
        
        right_panel = ttk.Frame(main_frame, style="Card.TFrame")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.setup_controls(left_panel)
        self.setup_results_display(right_panel)
        
    def setup_controls(self, parent):
        """Setup control panel"""
        control_frame = ttk.LabelFrame(parent, text="Control Panel", padding=18, style="Card.TLabelframe")
        control_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(control_frame, text="Source Currency", style="Heading.TLabel").pack(anchor="w", pady=(4, 6))
        ttk.Label(
            control_frame,
            text="Choose the base currency for path and cycle analysis.",
            style="Body.TLabel",
            wraplength=250,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.source_currency = ttk.Combobox(control_frame, values=self.graph.currencies, width=22, state="readonly")
        self.source_currency.set('USD')
        self.source_currency.pack(fill=tk.X, pady=(0, 16))
        
        ttk.Label(control_frame, text="Investment Amount ($)", style="Heading.TLabel").pack(anchor="w", pady=(0, 6))
        self.investment = ttk.Entry(control_frame, width=20)
        self.investment.insert(0, "1000")
        self.investment.pack(fill=tk.X, pady=(0, 16))
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=8)
        
        ttk.Button(control_frame, text="Detect Arbitrage", style="Accent.TButton",
                   command=self.detect_arbitrage).pack(pady=(14, 8), fill=tk.X)
        ttk.Button(control_frame, text="Show Shortest Paths", style="Secondary.TButton",
                   command=self.show_paths).pack(pady=6, fill=tk.X)
        ttk.Button(control_frame, text="Find Best Cycle", style="Secondary.TButton",
                   command=self.find_best).pack(pady=6, fill=tk.X)
        ttk.Button(control_frame, text="Export Results", style="Secondary.TButton",
                   command=self.export_results).pack(pady=6, fill=tk.X)
        ttk.Button(control_frame, text="Refresh Data", style="Secondary.TButton",
                   command=self.refresh_data).pack(pady=6, fill=tk.X)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=16)
        
        helper = tk.Label(
            control_frame,
            text="Tip: Start with 'Detect Arbitrage' to populate ranked cycles, then inspect paths and summaries.",
            font=("Segoe UI", 9),
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            wraplength=250,
            justify="left",
        )
        helper.pack(anchor="w", pady=(0, 12))

        self.status_label = ttk.Label(control_frame, text="Ready", style="Status.TLabel")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 2))
        
    def setup_results_display(self, parent):
        """Setup results display area"""
        header = tk.Frame(parent, bg=self.palette["panel"])
        header.pack(fill=tk.X, padx=18, pady=(18, 0))

        title = tk.Label(
            header,
            text="Analysis Workspace",
            font=("Segoe UI Semibold", 16),
            bg=self.palette["panel"],
            fg=self.palette["ink"],
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Use the tabs below to review cycles, paths, best opportunities, and overall market summary.",
            font=("Segoe UI", 10),
            bg=self.palette["panel"],
            fg=self.palette["muted"],
        )
        subtitle.pack(anchor="w", pady=(4, 10))

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))
        
        self.cycles_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cycles_frame, text="Arbitrage Cycles")
        self.cycles_text = self._create_text_panel(self.cycles_frame)
        self.cycles_text.pack(fill=tk.BOTH, expand=True)
        
        self.paths_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.paths_frame, text="Shortest Paths")
        self.paths_text = self._create_text_panel(self.paths_frame)
        self.paths_text.pack(fill=tk.BOTH, expand=True)
        
        self.best_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.best_frame, text="Best Opportunities")
        self.best_text = self._create_text_panel(self.best_frame)
        self.best_text.pack(fill=tk.BOTH, expand=True)
        
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Analysis Summary")
        self.summary_text = self._create_text_panel(self.summary_frame)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        self.show_summary()

    def _create_text_panel(self, parent):
        """Create a styled scrolled text area used by each analysis tab."""
        widget = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#fbfdff",
            fg=self.palette["ink"],
            insertbackground=self.palette["accent"],
            relief=tk.FLAT,
            borderwidth=0,
            padx=18,
            pady=16,
            spacing1=2,
            spacing3=4,
        )
        widget.configure(highlightthickness=1, highlightbackground=self.palette["line"])
        return widget
        
    def detect_arbitrage(self):
        """Run arbitrage detection"""
        self.status_label.config(text="Detecting arbitrage...")
        
        def run_detection():
            self.cycles_text.delete(1.0, tk.END)
            self.cycles_text.insert(tk.END, "SCANNING FOR ARBITRAGE OPPORTUNITIES\n")
            self.cycles_text.insert(tk.END, "="*50 + "\n\n")
            
            has_arb = self.detector.detect_arbitrage(self.source_currency.get())
            
            if has_arb:
                self.cycles_text.insert(tk.END, "[OK] ARBITRAGE OPPORTUNITIES FOUND!\n\n")
                profit_cycles = self.detector.get_profit_cycles()
                
                if profit_cycles:
                    for i, cycle in enumerate(profit_cycles[:20], 1):
                        self.cycles_text.insert(tk.END, f"CYCLE #{i}\n")
                        cycle_str = " -> ".join(cycle['cycle']) + " -> " + cycle['cycle'][0]
                        self.cycles_text.insert(tk.END, f"   {cycle_str}\n")
                        self.cycles_text.insert(tk.END, f"   Profit: {cycle['profit_percent']:.4f}%\n")
                        
                        inv = float(self.investment.get())
                        profit = inv * cycle['profit_percent'] / 100
                        self.cycles_text.insert(tk.END, f"   ${inv:,.2f} -> ${inv + profit:,.2f} (${profit:,.2f} profit)\n\n")
                else:
                    self.cycles_text.insert(tk.END, "   No profitable cycles found above threshold\n")
            else:
                self.cycles_text.insert(tk.END, "[INFO] No arbitrage opportunities detected.\n")
            
            self.status_label.config(text="Detection complete")
        
        threading.Thread(target=run_detection, daemon=True).start()
    
    def show_paths(self):
        """Show shortest paths from source"""
        self.status_label.config(text="Calculating shortest paths...")
        
        self.paths_text.delete(1.0, tk.END)
        source = self.source_currency.get()
        self.paths_text.insert(tk.END, f"SHORTEST PATHS FROM {source}\n")
        self.paths_text.insert(tk.END, "="*60 + "\n\n")
        
        distances, paths = self.detector.get_shortest_paths(source)
        
        self.paths_text.insert(tk.END, f"{'Currency':<10} {'Distance':<12} {'Profit %':<10} {'Path':<30}\n")
        self.paths_text.insert(tk.END, "-"*70 + "\n")
        
        count = 0
        for i, currency in enumerate(self.graph.currencies):
            if distances[i] != float('inf') and count < 20:
                profit = (math.exp(-distances[i]) - 1) * 100
                path_str = " -> ".join(paths[i][:5]) if paths[i] else "-"
                if len(paths[i]) > 5:
                    path_str += "..."
                self.paths_text.insert(tk.END, f"{currency:<10} {distances[i]:<12.6f} {profit:<10.2f}% {path_str:<30}\n")
                count += 1
        
        if len(self.graph.currencies) > 20:
            self.paths_text.insert(tk.END, f"\n... and {len(self.graph.currencies) - 20} more currencies\n")
        
        self.status_label.config(text="Paths displayed")
    
    def find_best(self):
        """Find and display best arbitrage opportunity"""
        self.status_label.config(text="Finding best opportunity...")
        
        self.best_text.delete(1.0, tk.END)
        self.best_text.insert(tk.END, "BEST ARBITRAGE OPPORTUNITIES\n")
        self.best_text.insert(tk.END, "="*60 + "\n\n")
        
        best = self.detector.find_best_arbitrage(float(self.investment.get()))
        
        if best:
            self.best_text.insert(tk.END, "MOST PROFITABLE CYCLE:\n\n")
            cycle_str = f"   {best['cycle'][0]} -> {best['cycle'][1]} -> {best['cycle'][2]} -> {best['cycle'][0]}\n"
            self.best_text.insert(tk.END, cycle_str)
            self.best_text.insert(tk.END, f"   Profit: {best['profit_percent']:.4f}%\n")
            self.best_text.insert(tk.END, f"   Investment: ${best.get('investment', 0):,.2f}\n")
            self.best_text.insert(tk.END, f"   Final Amount: ${best['final_amount']:,.2f}\n")
            self.best_text.insert(tk.END, f"   Net Profit: ${best['profit_amount']:,.2f}\n")
        else:
            self.best_text.insert(tk.END, "   No profitable cycles found\n")
        
        cycles = self.detector.get_profit_cycles()
        if cycles:
            self.best_text.insert(tk.END, "\n" + "="*60 + "\n")
            self.best_text.insert(tk.END, "TOP 5 ARBITRAGE CYCLES:\n\n")
            for i, cycle in enumerate(cycles[:5], 1):
                cycle_str = f"   {i}. {' -> '.join(cycle['cycle'])} -> {cycle['cycle'][0]}\n"
                self.best_text.insert(tk.END, cycle_str)
                self.best_text.insert(tk.END, f"      Profit: {cycle['profit_percent']:.4f}%\n")
        
        self.status_label.config(text="Best opportunity found")
    
    def show_summary(self):
        """Show analysis summary"""
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, "ANALYSIS SUMMARY\n")
        self.summary_text.insert(tk.END, "="*60 + "\n\n")
        
        self.summary_text.insert(tk.END, "GRAPH STATISTICS:\n")
        self.summary_text.insert(tk.END, f"   Currencies: {self.graph.get_num_currencies()}\n")
        self.summary_text.insert(tk.END, f"   Exchange Rates: {self.graph.get_num_edges()}\n\n")
        
        self.summary_text.insert(tk.END, "ALGORITHM COMPLEXITY:\n")
        V = self.graph.get_num_currencies()
        E = self.graph.get_num_edges()
        self.summary_text.insert(tk.END, f"   Time Complexity: O(V x E) = {V} x {E} = {V*E:,} operations\n")
        self.summary_text.insert(tk.END, f"   Space Complexity: O(V) = {V} units\n\n")
        
        self.summary_text.insert(tk.END, "ARBITRAGE DETECTION:\n")
        self.detector.detect_arbitrage(self.source_currency.get())
        cycles = self.detector.get_profit_cycles()
        self.summary_text.insert(tk.END, f"   Cycles Found: {len(cycles)}\n")
        
        if cycles:
            max_profit = max(c['profit_percent'] for c in cycles)
            avg_profit = sum(c['profit_percent'] for c in cycles) / len(cycles)
            self.summary_text.insert(tk.END, f"   Max Profit: {max_profit:.4f}%\n")
            self.summary_text.insert(tk.END, f"   Average Profit: {avg_profit:.4f}%\n\n")
        
        self.summary_text.insert(tk.END, "REAL-WORLD NOTES:\n")
        self.summary_text.insert(tk.END, "   - Transaction costs typically 0.1-0.5%\n")
        self.summary_text.insert(tk.END, "   - Need >0.1% profit to overcome costs\n")
        self.summary_text.insert(tk.END, "   - Arbitrage opportunities are usually <0.05% in real markets\n")
        self.summary_text.insert(tk.END, "   - High-frequency trading firms compete for these opportunities\n")
    
    def export_results(self):
        """Export results to file"""
        import os
        from currency_arbitrage.utils import get_output_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(get_output_dir("text"), f"arbitrage_results_{timestamp}.txt")
        
        try:
            with open(filename, 'w') as f:
                f.write("CURRENCY ARBITRAGE DETECTOR RESULTS\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("="*60 + "\n\n")
                
                f.write("ARBITRAGE CYCLES:\n")
                f.write("-"*40 + "\n")
                
                self.detector.detect_arbitrage(self.source_currency.get())
                cycles = self.detector.get_profit_cycles()
                
                if cycles:
                    for i, cycle in enumerate(cycles[:50], 1):
                        f.write(f"\nCycle #{i}: {' -> '.join(cycle['cycle'])} -> {cycle['cycle'][0]}\n")
                        f.write(f"  Profit: {cycle['profit_percent']:.4f}%\n")
                        f.write(f"  Gross Return: {cycle['total_product']:.6f}\n")
                else:
                    f.write("No arbitrage cycles found\n")
                
                f.write("\n\nSHORTEST PATHS:\n")
                f.write("-"*40 + "\n")
                distances, paths = self.detector.get_shortest_paths(self.source_currency.get())
                
                for i, currency in enumerate(self.graph.currencies[:20]):
                    if distances[i] != float('inf'):
                        profit = (math.exp(-distances[i]) - 1) * 100
                        path_str = " -> ".join(paths[i]) if paths[i] else "-"
                        f.write(f"{currency}: {profit:.4f}% profit, Path: {path_str}\n")
            
            messagebox.showinfo("Export Complete", f"Results saved to {filename}")
            self.status_label.config(text=f"Exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def refresh_data(self):
        """Refresh graph data"""
        self.status_label.config(text="Refreshing data...")
        self.show_summary()
        messagebox.showinfo("Info", "Data refreshed. Run detection again for new results.")
        self.status_label.config(text="Ready")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
