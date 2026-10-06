import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from File_organization import (
    FILE_TYPES,
    SYSTEM_FOLDERS,
    get_category,
    organize_folder,
    undo_last,
    list_loose_files,
    find_duplicates,
    delete_file,
    get_history,
    get_operation_moves,
)


class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic File Organizer")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 650)

        self.selected_folder = ""
        self.auto_mode_on = False
        self.auto_job = None
        self.dark_mode = False

        self.colors = {}
        self.setup_colors()

        self.sidebar = None
        self.content = None
        self.status_label = None
        self.status_dot = None

        self.build_window()
        self.show_dashboard()

    
    def setup_colors(self):
        if self.dark_mode:
            self.colors = {
                "bg": "#171a1f",
                "sidebar": "#20242a",
                "card": "#22272e",
                "border": "#343a43",
                "text": "#f3f4f6",
                "muted": "#a0a7b1",
                "green": "#36b96f",
                "green_hover": "#2e9d5e",
                "blue": "#3b8ed0",
                "blue_hover": "#3277b0",
                "red": "#d95c57",
                "red_hover": "#bd4d49",
                "accent": "#2eaa8b",
                "accent_hover": "#278f76",
                "log_bg": "#101317",
                "log_text": "#8be28f",
                "selected": "#dff4e8",
                "selected_text": "#14532d",
            }
        else:
            self.colors = {
                "bg": "#f5f7f8",
                "sidebar": "#ffffff",
                "card": "#ffffff",
                "border": "#e2e7ea",
                "text": "#17212b",
                "muted": "#6b7280",
                "green": "#2fa866",
                "green_hover": "#278d57",
                "blue": "#3988c9",
                "blue_hover": "#3073aa",
                "red": "#d9534f",
                "red_hover": "#c64743",
                "accent": "#2eaa78",
                "accent_hover": "#258d64",
                "log_bg": "#1d2228",
                "log_text": "#8be28f",
                "selected": "#e5f5eb",
                "selected_text": "#166534",
            }

    def apply_theme(self):
        self.setup_colors()
        self.root.configure(bg=self.colors["bg"])
        self.build_window()
        self.show_dashboard()

    
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def make_card(self, parent, **kwargs):
        options = {
            "bg": self.colors["card"],
            "highlightbackground": self.colors["border"],
            "highlightthickness": 1,
            "bd": 0,
        }
        options.update(kwargs)
        return tk.Frame(parent, **options)

    def make_button(self, parent, text, command, color=None,
                    hover=None, width=None):
        color = color or self.colors["accent"]
        hover = hover or self.colors["accent_hover"]

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=hover,
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=9,
        )

        if width:
            btn.config(width=width)

        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def label(self, parent, text, size=10, bold=False,
              color=None, **kwargs):
        font = ("Segoe UI", size, "bold" if bold else "normal")
        return tk.Label(
            parent,
            text=text,
            font=font,
            fg=color or self.colors["text"],
            bg=kwargs.pop("bg", parent.cget("bg")),
            **kwargs
        )

    def set_status(self, text, color=None):
        if self.status_label and self.status_label.winfo_exists():
            self.status_label.config(text=text)
        if self.status_dot and self.status_dot.winfo_exists():
            self.status_dot.config(fg=color or self.colors["muted"])

   
    def build_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        
        self.sidebar = tk.Frame(
            self.root,
            bg=self.colors["sidebar"],
            width=225,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=self.colors["sidebar"])
        logo.pack(fill="x", padx=18, pady=(24, 18))

        tk.Label(
            logo,
            text="▣",
            font=("Segoe UI Symbol", 24),
            bg=self.colors["sidebar"],
            fg=self.colors["green"],
        ).pack(side="left")

        tk.Label(
            logo,
            text="Auto Organize",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["text"],
        ).pack(side="left", padx=9)

        nav = [
            ("⌂", "Dashboard", self.show_dashboard),
            ("▣", "Source Folder", self.show_source),
            ("▶", "Organize Now", self.show_organize),
            ("☷", "Rules", self.show_rules),
            ("▤", "Duplicates", self.show_duplicates),
            ("▤", "Logs", self.show_logs),
            ("⚙", "Settings", self.show_settings),
            ("ⓘ", "About", self.show_about),
        ]

        self.nav_buttons = []

        for icon, name, command in nav:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}   {name}",
                command=command,
                anchor="w",
                bg=self.colors["sidebar"],
                fg=self.colors["text"],
                activebackground=self.colors["selected"],
                activeforeground=self.colors["selected_text"],
                font=("Segoe UI", 10),
                relief="flat",
                bd=0,
                padx=18,
                pady=11,
                cursor="hand2",
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_buttons.append((name, btn))

        spacer = tk.Frame(self.sidebar, bg=self.colors["sidebar"])
        spacer.pack(fill="both", expand=True)

        bottom = tk.Frame(self.sidebar, bg=self.colors["sidebar"])
        bottom.pack(fill="x", padx=18, pady=18)

        tk.Label(
            bottom,
            text="●",
            font=("Segoe UI", 10),
            bg=self.colors["sidebar"],
            fg=self.colors["green"],
        ).pack(side="left")

        tk.Label(
            bottom,
            text=" Ready",
            font=("Segoe UI", 9),
            bg=self.colors["sidebar"],
            fg=self.colors["muted"],
        ).pack(side="left")

        
        self.content = tk.Frame(
            self.root,
            bg=self.colors["bg"],
        )
        self.content.pack(side="left", fill="both", expand=True)

        
        status = tk.Frame(
            self.content,
            bg=self.colors["card"],
            height=34,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)

        self.status_dot = tk.Label(
            status,
            text="●",
            font=("Segoe UI", 9),
            bg=self.colors["card"],
            fg=self.colors["muted"],
        )
        self.status_dot.pack(side="left", padx=(16, 5))

        self.status_label = tk.Label(
            status,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.colors["card"],
            fg=self.colors["muted"],
        )
        self.status_label.pack(side="left")

    def set_active_nav(self, active_name):
        for name, btn in self.nav_buttons:
            if name == active_name:
                btn.config(
                    bg=self.colors["selected"],
                    fg=self.colors["selected_text"],
                )
            else:
                btn.config(
                    bg=self.colors["sidebar"],
                    fg=self.colors["text"],
                )

  
    def build_header(self, title, subtitle, action_text=None,
                     action_command=None):
        header = tk.Frame(self.content, bg=self.colors["bg"])
        header.pack(fill="x", padx=30, pady=(25, 16))

        left = tk.Frame(header, bg=self.colors["bg"])
        left.pack(side="left", fill="x", expand=True)

        self.label(
            left, title, 21, True, self.colors["text"]
        ).pack(anchor="w")

        self.label(
            left, subtitle, 10, False, self.colors["muted"]
        ).pack(anchor="w", pady=(3, 0))

        if action_text:
            self.make_button(
                header,
                action_text,
                action_command,
                self.colors["green"],
                self.colors["green_hover"],
            ).pack(side="right", padx=(15, 0))

    
    def show_dashboard(self):
        self.set_active_nav("Dashboard")
        self.clear_content()

        self.build_header(
            "Welcome back! 👋",
            "Let's make your files neat and organized.",
            "Organize Now  ▶",
            self.show_organize,
        )

        stats = self.get_stats()

        stat_row = tk.Frame(self.content, bg=self.colors["bg"])
        stat_row.pack(fill="x", padx=30, pady=(0, 16))

        stat_data = [
            ("▣", "Files in Source", str(stats["files"])),
            ("▤", "Operations", str(stats["operations"])),
            ("✓", "Last Activity", stats["last"]),
        ]

        for icon, title, value in stat_data:
            card = self.make_card(stat_row)
            card.pack(side="left", fill="both", expand=True, padx=5)

            top = tk.Frame(card, bg=self.colors["card"])
            top.pack(fill="x", padx=15, pady=(14, 3))

            tk.Label(
                top,
                text=icon,
                font=("Segoe UI Symbol", 19),
                bg=self.colors["card"],
                fg=self.colors["green"],
            ).pack(side="left")

            self.label(
                top, title, 9, False, self.colors["muted"],
                bg=self.colors["card"]
            ).pack(side="left", padx=9)

            self.label(
                card, value, 16, True, self.colors["text"],
                bg=self.colors["card"]
            ).pack(anchor="w", padx=52, pady=(0, 14))

        
        overview = self.make_card(self.content)
        overview.pack(fill="x", padx=30, pady=(0, 16))

        self.label(
            overview, "Quick Overview", 12, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(14, 10))

        categories = [
            ("Pictures", "▴"),
            ("Documents", "▤"),
            ("Videos", "▶"),
            ("Music", "♫"),
            ("Archives", "□"),
            ("Code", "</>"),
            ("Others", "…"),
        ]

        category_row = tk.Frame(overview, bg=self.colors["card"])
        category_row.pack(fill="x", padx=12, pady=(0, 15))

        counts = self.get_category_counts()

        for category, icon in categories:
            box = tk.Frame(
                category_row,
                bg=self.colors["card"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
            )
            box.pack(side="left", fill="both", expand=True, padx=3)

            tk.Label(
                box,
                text=icon,
                font=("Segoe UI", 15, "bold"),
                bg=self.colors["card"],
                fg=self.colors["accent"],
            ).pack(pady=(9, 1))

            self.label(
                box, category, 8, False, self.colors["muted"],
                bg=self.colors["card"]
            ).pack()

            self.label(
                box, str(counts.get(category, 0)), 12, True,
                bg=self.colors["card"]
            ).pack(pady=(1, 9))

       
        activity = self.make_card(self.content)
        activity.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        title_row = tk.Frame(activity, bg=self.colors["card"])
        title_row.pack(fill="x", padx=18, pady=(14, 8))

        self.label(
            title_row, "Recent Activity", 12, True,
            bg=self.colors["card"]
        ).pack(side="left")

        tk.Button(
            title_row,
            text="View Details",
            command=self.show_logs,
            bg=self.colors["card"],
            fg=self.colors["green"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["green"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(side="right")

        records = get_history(limit=6)

        if not records:
            self.label(
                activity,
                "No organization activity yet. Select a source folder to begin.",
                10, False, self.colors["muted"],
                bg=self.colors["card"]
            ).pack(anchor="w", padx=18, pady=20)
        else:
            for record in records:
                row = tk.Frame(activity, bg=self.colors["card"])
                row.pack(fill="x", padx=18, pady=5)

                tk.Label(
                    row,
                    text="●",
                    font=("Segoe UI", 9),
                    bg=self.colors["card"],
                    fg=self.colors["green"]
                ).pack(side="left")

                message = (
                    f"{record['operation_type'].title()} — "
                    f"{record['moved_count']} moved, "
                    f"{record['skipped_count']} skipped, "
                    f"{record['duplicate_count']} duplicates"
                )

                self.label(
                    row, message, 9, False, self.colors["text"],
                    bg=self.colors["card"]
                ).pack(side="left", padx=9)

                time_text = record["completed_at"] or record["started_at"]
                self.label(
                    row, time_text.replace("T", " "), 8, False,
                    self.colors["muted"], bg=self.colors["card"]
                ).pack(side="right")

    def get_stats(self):
        files = (
            len(list_loose_files(self.selected_folder))
            if self.selected_folder else 0
        )

        all_records = get_history(limit=1000)
        records = [
            record for record in all_records
            if (
                not self.selected_folder
                or os.path.normcase(os.path.normpath(record.get("source_folder", "")))
                == os.path.normcase(os.path.normpath(self.selected_folder))
            )
        ]

        operations = len(records)

        
        if self.selected_folder:
            try:
                duplicate_count = len(find_duplicates(self.selected_folder))
            except Exception:
                duplicate_count = 0
        else:
            duplicate_count = 0

        if records:
            last = records[0]["completed_at"] or records[0]["started_at"]
            last = last.replace("T", " ")
        else:
            last = "None"

        return {
            "files": files,
            "operations": operations,
            "duplicates": duplicate_count,
            "last": last,
        }

    def get_category_counts(self):
        
        counts = {
            "Pictures": 0,
            "Documents": 0,
            "Videos": 0,
            "Music": 0,
            "Archives": 0,
            "Code": 0,
            "Others": 0,
        }

        if not self.selected_folder:
            return counts

        try:
            records = get_history(limit=1000)

            selected = os.path.normcase(os.path.normpath(self.selected_folder))

            for record in records:
                source = record.get("source_folder", "")
                if os.path.normcase(os.path.normpath(source)) != selected:
                    continue

                
                if record.get("status") == "undone":
                    continue

                for move in get_operation_moves(record["id"]):
                    category = move.get("category")
                    if category in counts:
                        counts[category] += 1

        except Exception:
            pass

        return counts

    
    def show_source(self):
        self.set_active_nav("Source Folder")
        self.clear_content()

        self.build_header(
            "Source Folder",
            "Choose the folder whose loose files you want to organize."
        )

        card = self.make_card(self.content)
        card.pack(fill="x", padx=30, pady=5)

        self.label(
            card, "Selected folder", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(16, 7))

        row = tk.Frame(card, bg=self.colors["card"])
        row.pack(fill="x", padx=18, pady=(0, 10))

        self.folder_var = tk.StringVar(
            value=self.selected_folder or "No folder selected"
        )

        entry = tk.Entry(
            row,
            textvariable=self.folder_var,
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            relief="flat",
            bd=0,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=9)

        self.make_button(
            row,
            "📁  Browse",
            self.browse_folder,
            self.colors["accent"],
            self.colors["accent_hover"],
        ).pack(side="right", padx=(10, 0))

        self.preview_source_files(card)

        actions = tk.Frame(self.content, bg=self.colors["bg"])
        actions.pack(fill="x", padx=30, pady=16)

        self.make_button(
            actions, "👁  Preview Changes",
            self.run_preview,
            self.colors["blue"],
            self.colors["blue_hover"],
        ).pack(side="left", padx=(0, 8))

        self.make_button(
            actions, "Organize Now  ▶",
            self.run_organize,
            self.colors["green"],
            self.colors["green_hover"],
        ).pack(side="left", padx=8)

    def preview_source_files(self, parent):
        if self.selected_folder:
            files = list_loose_files(self.selected_folder)
            if files:
                text = (
                    f"{len(files)} file(s) found directly inside this folder.\n\n"
                    + "\n".join(f"• {name}" for name in files[:12])
                )
                if len(files) > 12:
                    text += f"\n• ... and {len(files) - 12} more"
            else:
                text = "This folder has no loose files to organize."
        else:
            text = "Select a folder to see its files."

        self.label(
            parent, "Folder Preview", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(8, 5))

        box = tk.Text(
            parent,
            height=12,
            wrap="word",
            font=("Consolas", 9),
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
        )
        box.pack(fill="x", padx=18, pady=(0, 18))
        box.insert("1.0", text)
        box.config(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select Folder to Organize"
        )

        if not folder:
            return

        self.selected_folder = os.path.normpath(folder)
        self.set_status("Folder selected.", self.colors["green"])
        self.show_source()

    
    def show_organize(self):
        self.set_active_nav("Organize Now")
        self.clear_content()

        self.build_header(
            "Organize Now",
            "Preview first, then safely organize the selected folder."
        )

        # Selected folder card
        folder_card = self.make_card(self.content)
        folder_card.pack(fill="x", padx=30, pady=(0, 14))

        self.label(
            folder_card, "Source Folder", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(15, 5))

        path = self.selected_folder or "No folder selected"
        self.label(
            folder_card, path, 10, False,
            self.colors["text"] if self.selected_folder else self.colors["muted"],
            bg=self.colors["card"],
            wraplength=850,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        # Main action cards
        actions = tk.Frame(self.content, bg=self.colors["bg"])
        actions.pack(fill="x", padx=30, pady=2)

        cards = [
            (
                "👁",
                "Preview Changes",
                "See what will be moved without changing any files.",
                self.run_preview,
                self.colors["blue"],
                self.colors["blue_hover"],
            ),
            (
                "▶",
                "Organize Files",
                "Run the existing backend organization logic.",
                self.run_organize,
                self.colors["green"],
                self.colors["green_hover"],
            ),
            (
                "↩",
                "Undo Last",
                "Restore files from the latest completed operation.",
                self.run_undo,
                self.colors["red"],
                self.colors["red_hover"],
            ),
        ]

        for icon, title, desc, command, color, hover in cards:
            card = self.make_card(actions)
            card.pack(side="left", fill="both", expand=True, padx=5)

            tk.Label(
                card,
                text=icon,
                font=("Segoe UI Symbol", 22),
                bg=self.colors["card"],
                fg=color,
            ).pack(anchor="w", padx=18, pady=(16, 3))

            self.label(
                card, title, 11, True,
                bg=self.colors["card"]
            ).pack(anchor="w", padx=18)

            self.label(
                card, desc, 8, False,
                self.colors["muted"],
                bg=self.colors["card"],
                wraplength=250,
                justify="left",
            ).pack(anchor="w", padx=18, pady=(4, 12))

            self.make_button(
                card, title, command, color, hover
            ).pack(fill="x", padx=18, pady=(0, 16))

        # Auto organize
        auto = self.make_card(self.content)
        auto.pack(fill="x", padx=30, pady=18)

        left = tk.Frame(auto, bg=self.colors["card"])
        left.pack(side="left", fill="x", expand=True, padx=18, pady=16)

        self.label(
            left, "Automatic Organization", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w")

        self.label(
            left,
            "When enabled, the selected folder is checked every few seconds.",
            9, False, self.colors["muted"],
            bg=self.colors["card"]
        ).pack(anchor="w", pady=(4, 0))

        button_text = (
            "⏸  Stop Auto-Organize"
            if self.auto_mode_on
            else "▶  Start Auto-Organize"
        )

        self.auto_button = self.make_button(
            auto,
            button_text,
            self.toggle_auto_mode,
            self.colors["red"] if self.auto_mode_on else self.colors["accent"],
            self.colors["red_hover"] if self.auto_mode_on else self.colors["accent_hover"],
        )
        self.auto_button.pack(side="right", padx=18, pady=20)

        # Activity
        self.label(
            self.content, "Current Activity", 11, True
        ).pack(anchor="w", padx=30, pady=(0, 7))

        self.create_log_box(self.content, height=10)

    def create_log_box(self, parent, height=10):
        self.output_box = scrolledtext.ScrolledText(
            parent,
            height=height,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
        )
        self.output_box.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 15)
        )

    def log(self, message):
        if hasattr(self, "output_box") and self.output_box.winfo_exists():
            self.output_box.insert(tk.END, message + "\n")
            self.output_box.see(tk.END)
            self.root.update_idletasks()

    def ensure_folder(self):
        if not self.selected_folder:
            messagebox.showwarning(
                "Select Folder",
                "Please select a source folder first."
            )
            return False
        return True

    def run_preview(self):
        if not self.ensure_folder():
            return

        self.show_organize()
        self.log("Running preview — no files will be moved...\n")

        try:
            result = organize_folder(
                self.selected_folder,
                log_callback=self.log,
                dry_run=True
            )

            self.log("\nPreview finished.")
            self.log(
                f"Files that can be moved: {result.get('moved', 0)}"
            )
            self.log(
                f"Skipped: {result.get('skipped', 0)}"
            )
            self.log(
                f"Duplicates: {result.get('duplicates', 0)}"
            )

            self.set_status("Preview complete.", self.colors["blue"])

        except Exception as error:
            self.log(f"❌ Preview error: {error}")
            self.set_status("Preview failed.", self.colors["red"])

    def run_organize(self):
        if not self.ensure_folder():
            return

        confirmed = messagebox.askyesno(
            "Confirm Organization",
            "Organize the files now?\n\n"
            "Pictures → Windows Pictures\n"
            "Documents → Windows Documents\n"
            "Videos → Windows Videos\n"
            "Music → Windows Music\n\n"
            "Archives, Code and Others → inside the selected folder."
        )

        if not confirmed:
            return

        self.show_organize()
        self.log("Starting organization...\n")

        try:
            result = organize_folder(
                self.selected_folder,
                log_callback=self.log,
                dry_run=False
            )

            moved = result.get("moved", 0)
            skipped = result.get("skipped", 0)
            duplicates = result.get("duplicates", 0)

            self.log("\nActivity saved to local SQLite history.")
            self.log(
                f"\nSummary: {moved} moved | "
                f"{skipped} skipped | "
                f"{duplicates} duplicates"
            )

            self.set_status(
                f"Done — {moved} file(s) moved.",
                self.colors["green"]
            )

            messagebox.showinfo(
                "Organization Complete",
                f"Organization complete!\n\n"
                f"Moved: {moved}\n"
                f"Skipped: {skipped}\n"
                f"Duplicates: {duplicates}"
            )

            

        except Exception as error:
            self.log(f"❌ Organization error: {error}")
            self.set_status(
                "Organization failed.",
                self.colors["red"]
            )
            messagebox.showerror(
                "Organization Error",
                f"An error occurred:\n\n{error}"
            )

    def run_undo(self):
        if not self.ensure_folder():
            return

        confirmed = messagebox.askyesno(
            "Undo Organization",
            "Undo the most recent organization operation for this folder?"
        )

        if not confirmed:
            return

        self.show_organize()
        self.log("Undoing the latest organization...\n")

        try:
            restored = undo_last(
                self.selected_folder,
                log_callback=self.log
            )

            self.log(f"\nUndo complete — {restored} file(s) restored.")
            self.set_status(
                f"Undo complete — {restored} file(s) restored.",
                self.colors["blue"]
            )

    

        except Exception as error:
            self.log(f"❌ Undo error: {error}")
            self.set_status("Undo failed.", self.colors["red"])
            messagebox.showerror(
                "Undo Error",
                f"An error occurred while undoing:\n\n{error}"
            )

    
    def toggle_auto_mode(self):
        if not self.ensure_folder():
            return

        self.auto_mode_on = not self.auto_mode_on

        if self.auto_mode_on:
            self.set_status(
                "Auto-Organize is ON — watching folder...",
                self.colors["green"]
            )
            self.schedule_auto_check()
        else:
            if self.auto_job:
                self.root.after_cancel(self.auto_job)
                self.auto_job = None

            self.set_status(
                "Auto-Organize is OFF.",
                self.colors["muted"]
            )

        self.show_organize()

    def schedule_auto_check(self):
        if not self.auto_mode_on:
            return

        self.auto_job = self.root.after(
            4000,
            self.check_auto_folder
        )

    def check_auto_folder(self):
        if not self.auto_mode_on:
            return

        try:
            loose_files = list_loose_files(self.selected_folder)

            if loose_files:
                # Use the existing backend exactly as before.
                organize_folder(
                    self.selected_folder,
                    log_callback=self.log if hasattr(self, "output_box") else print,
                    dry_run=False
                )

                self.set_status(
                    "Auto-Organize moved new file(s).",
                    self.colors["green"]
                )

        except Exception as error:
            if hasattr(self, "output_box"):
                self.log(f"[Auto] Error: {error}")

        self.schedule_auto_check()

    
    def show_rules(self):
        self.set_active_nav("Rules")
        self.clear_content()

        self.build_header(
            "Organization Rules",
            "These are the rules already defined in File_organization.py."
        )

        info = self.make_card(self.content)
        info.pack(fill="x", padx=30, pady=(0, 14))

        self.label(
            info,
            "No backend rules were changed by this GUI.",
            9, False, self.colors["muted"],
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=12)

        canvas_frame = tk.Frame(self.content, bg=self.colors["bg"])
        canvas_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=canvas.yview
        )
        inner = tk.Frame(canvas, bg=self.colors["bg"])

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0), window=inner, anchor="nw"
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for category, extensions in FILE_TYPES.items():
            card = self.make_card(inner)
            card.pack(fill="x", pady=5)

            self.label(
                card, category, 11, True,
                bg=self.colors["card"]
            ).pack(anchor="w", padx=16, pady=(12, 4))

            destination = SYSTEM_FOLDERS.get(
                category,
                f"Inside selected folder → {category}"
            )

            self.label(
                card,
                f"Destination: {destination}",
                9, False, self.colors["muted"],
                bg=self.colors["card"],
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=16)

            self.label(
                card,
                "Extensions: " + ", ".join(extensions),
                9, False, self.colors["text"],
                bg=self.colors["card"],
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(4, 12))

        others = self.make_card(inner)
        others.pack(fill="x", pady=5)

        self.label(
            others, "Others", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.label(
            others,
            "Files that do not match a listed extension → "
            "Others folder inside the selected source folder.",
            9, False, self.colors["muted"],
            bg=self.colors["card"],
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

    
    def show_duplicates(self):
        self.set_active_nav("Duplicates")
        self.clear_content()

        self.build_header(
            "Duplicate Files",
            "Scan the selected source folder and remove selected duplicates."
        )

        top = self.make_card(self.content)
        top.pack(fill="x", padx=30, pady=(0, 14))

        self.label(
            top,
            self.selected_folder or "No folder selected",
            9, False,
            self.colors["text"] if self.selected_folder else self.colors["muted"],
            bg=self.colors["card"],
            wraplength=800,
        ).pack(side="left", padx=18, pady=15)

        self.make_button(
            top,
            "♻  Scan Duplicates",
            self.run_duplicate_scan,
            self.colors["blue"],
            self.colors["blue_hover"],
        ).pack(side="right", padx=18, pady=10)

        self.duplicate_area = tk.Frame(
            self.content,
            bg=self.colors["bg"]
        )
        self.duplicate_area.pack(
            fill="both", expand=True, padx=30, pady=(0, 20)
        )

        self.label(
            self.duplicate_area,
            "Click “Scan Duplicates” to start.",
            10, False, self.colors["muted"]
        ).pack(anchor="w", pady=20)

    def run_duplicate_scan(self):
        if not self.ensure_folder():
            return

        try:
            groups = find_duplicates(self.selected_folder)
            self.display_duplicate_groups(groups)

            self.set_status(
                f"{len(groups)} duplicate group(s) found.",
                self.colors["blue"]
            )

        except Exception as error:
            messagebox.showerror(
                "Duplicate Error",
                f"Could not scan for duplicates:\n\n{error}"
            )

    def display_duplicate_groups(self, groups):
        for widget in self.duplicate_area.winfo_children():
            widget.destroy()

        if not groups:
            self.label(
                self.duplicate_area,
                "✓ No duplicate files found.",
                11, True, self.colors["green"]
            ).pack(anchor="w", pady=20)
            return

        self.label(
            self.duplicate_area,
            f"{len(groups)} duplicate group(s) found.",
            11, True
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(
            self.duplicate_area,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.duplicate_area,
            orient="vertical",
            command=canvas.yview
        )
        inner = tk.Frame(canvas, bg=self.colors["bg"])

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        checkbox_data = []

        for index, group in enumerate(groups, 1):
            card = self.make_card(inner)
            card.pack(fill="x", pady=5)

            self.label(
                card,
                f"Duplicate Group {index}",
                10, True,
                bg=self.colors["card"]
            ).pack(anchor="w", padx=14, pady=(11, 5))

            for file_path in group:
                var = tk.BooleanVar(value=False)
                checkbox_data.append((var, file_path))

                try:
                    size = os.path.getsize(file_path) / (1024 * 1024)
                except OSError:
                    size = 0

                check = tk.Checkbutton(
                    card,
                    text=f"{os.path.basename(file_path)}  |  {size:.2f} MB\n{file_path}",
                    variable=var,
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    activebackground=self.colors["card"],
                    activeforeground=self.colors["text"],
                    selectcolor=self.colors["card"],
                    anchor="w",
                    justify="left",
                    font=("Segoe UI", 9),
                )
                check.pack(fill="x", padx=14, pady=3)

        bottom = tk.Frame(self.duplicate_area, bg=self.colors["bg"])
        bottom.pack(fill="x", pady=(10, 0))

        def delete_selected():
            selected = [
                path for var, path in checkbox_data if var.get()
            ]

            if not selected:
                messagebox.showwarning(
                    "No Selection",
                    "Select duplicate files to delete."
                )
                return

            confirmed = messagebox.askyesno(
                "Confirm Deletion",
                f"Delete {len(selected)} selected duplicate file(s)?\n\n"
                "This cannot be undone by the organization Undo button."
            )

            if not confirmed:
                return

            deleted = 0

            for path in selected:
                try:
                    if delete_file(path):
                        deleted += 1
                except Exception:
                    pass

            messagebox.showinfo(
                "Duplicates Removed",
                f"{deleted} duplicate file(s) deleted."
            )

            self.show_duplicates()

        self.make_button(
            bottom,
            "🗑  Delete Selected",
            delete_selected,
            self.colors["red"],
            self.colors["red_hover"],
        ).pack(side="right")

    def show_logs(self):
        self.set_active_nav("Logs")
        self.clear_content()

        self.build_header(
            "Activity Logs",
            "Recent organization operations stored by the existing SQLite history."
        )

        card = self.make_card(self.content)
        card.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        history_box = scrolledtext.ScrolledText(
            card,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            padx=12,
            pady=12,
        )
        history_box.pack(fill="both", expand=True, padx=15, pady=15)

        try:
            records = get_history(limit=100)

            if not records:
                history_box.insert(
                    tk.END,
                    "No history yet.\n"
                )
            else:
                for record in records:
                    history_box.insert(
                        tk.END,
                        "=" * 78 + "\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Operation #{record['id']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Type       : {record['operation_type']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Source     : {record['source_folder']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Started    : {record['started_at']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Completed  : {record['completed_at'] or '-'}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Status     : {record['status']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Moved      : {record['moved_count']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Skipped    : {record['skipped_count']}\n"
                    )
                    history_box.insert(
                        tk.END,
                        f"Duplicates : {record['duplicate_count']}\n"
                    )

                    moves = get_operation_moves(record["id"])

                    if moves:
                        history_box.insert(
                            tk.END,
                            "\nFiles moved:\n"
                        )
                        for move in moves:
                            history_box.insert(
                                tk.END,
                                f"  • {move['file_name']} → "
                                f"{move['category']}\n"
                            )

                    history_box.insert(tk.END, "\n")

        except Exception as error:
            history_box.insert(
                tk.END,
                f"Could not load history:\n{error}\n"
            )

        history_box.config(state="disabled")

    
    def show_settings(self):
        self.set_active_nav("Settings")
        self.clear_content()

        self.build_header(
            "Settings",
            "Appearance options for the GUI."
        )

        card = self.make_card(self.content)
        card.pack(fill="x", padx=30, pady=(0, 15))

        self.label(
            card, "Appearance", 12, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(16, 5))

        self.label(
            card,
            "Change the visual theme. This does not change file organization logic.",
            9, False, self.colors["muted"],
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(0, 12))

        mode_var = tk.BooleanVar(value=self.dark_mode)

        check = tk.Checkbutton(
            card,
            text="Use Dark Mode",
            variable=mode_var,
            command=lambda: self.change_theme(mode_var.get()),
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["text"],
            selectcolor=self.colors["card"],
            font=("Segoe UI", 10),
        )
        check.pack(anchor="w", padx=18, pady=(0, 18))

        note = self.make_card(self.content)
        note.pack(fill="x", padx=30)

        self.label(
            note, "Backend protection", 11, True,
            bg=self.colors["card"]
        ).pack(anchor="w", padx=18, pady=(16, 5))

        self.label(
            note,
            "The GUI continues to call File_organization.py for organizing, "
            "duplicate detection, deletion, history and undo.",
            9, False, self.colors["muted"],
            bg=self.colors["card"],
            wraplength=850,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

    def change_theme(self, enabled):
        self.dark_mode = enabled
        self.apply_theme()

    
    def show_about(self):
        self.set_active_nav("About")
        self.clear_content()

        self.build_header(
            "About Automatic File Organizer",
            "A simple desktop GUI for keeping files organized."
        )

        card = self.make_card(self.content)
        card.pack(fill="x", padx=30, pady=10)

        tk.Label(
            card,
            text="▣",
            font=("Segoe UI Symbol", 48),
            bg=self.colors["card"],
            fg=self.colors["green"],
        ).pack(pady=(25, 5))

        self.label(
            card,
            "Automatic File Organizer",
            18, True,
            bg=self.colors["card"]
        ).pack()

        self.label(
            card,
            "Built with Python + Tkinter",
            10, False, self.colors["muted"],
            bg=self.colors["card"]
        ).pack(pady=(4, 20))

        features = [
            "• Select a source folder",
            "• Preview organization before moving files",
            "• Organize files by extension",
            "• Detect duplicate files using the existing backend",
            "• View organization history",
            "• Undo the latest completed organization",
            "• Automatically watch a selected folder",
            "• Light / Dark GUI theme",
        ]

        for item in features:
            self.label(
                card, item, 10, False,
                bg=self.colors["card"]
            ).pack(anchor="w", padx=80, pady=3)

        self.label(
            card,
            "\nThe backend logic and SQLite history are kept unchanged.",
            9, False, self.colors["muted"],
            bg=self.colors["card"]
        ).pack(pady=(12, 25))

    
def main():
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
