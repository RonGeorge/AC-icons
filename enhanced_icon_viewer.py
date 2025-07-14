import sqlite3
from PIL import Image, ImageTk
import io
import tkinter as tk
from tkinter import ttk, messagebox
import math
import json

# ==============================================
# CUSTOMIZATION SETTINGS
# ==============================================

DB_PATH = "enhanced_icons.db"
COLUMNS = 8
ROWS = 4
ICON_WIDTH = 64
ICON_HEIGHT = 64
CELL_WIDTH = 100
CELL_HEIGHT = 120
PADX = 5
PADY = 5
TEXT_WRAPLENGTH = CELL_WIDTH - 10
WINDOW_TITLE = "Enhanced AC Icon Viewer"
WINDOW_SIZE = f"{CELL_WIDTH * COLUMNS + 100}x{CELL_HEIGHT * ROWS + 200}"
BG_COLOR = "#252526"
FONT_FAMILY = "Segoe UI"
TITLE_FONT_SIZE = 9
STATUS_FONT_SIZE = 9
FONT_COLOR = "#FFFFFF"

# ==============================================
# MAIN APPLICATION
# ==============================================

class EnhancedIconViewer:
    def __init__(self, root):
        self.root = root
        self.current_page = 1
        self.total_icons = 0
        
        # Configure window
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG_COLOR)
        
        # Create styles
        self.setup_styles()
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()
        self.load_data()
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, font=(FONT_FAMILY, TITLE_FONT_SIZE), foreground=FONT_COLOR)
        style.configure("Status.TLabel", font=(FONT_FAMILY, STATUS_FONT_SIZE), foreground=FONT_COLOR)
        
    def setup_ui(self):
        # Search Frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=PADX)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=PADX)
        self.search_entry.bind("<Return>", lambda e: self.search_icons())
        
        ttk.Button(search_frame, text="Search", command=self.search_icons).pack(side=tk.LEFT, padx=PADX)
        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT)

        # Results Grid Frame
        self.grid_frame = ttk.Frame(self.main_frame)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Create fixed grid cells with top-aligned icons
        self.cells = []
        for row in range(ROWS):
            row_cells = []
            for col in range(COLUMNS):
                # Cell container
                cell = ttk.Frame(self.grid_frame, width=CELL_WIDTH, height=CELL_HEIGHT)
                cell.grid(row=row, column=col, padx=PADX, pady=PADY, sticky="nsew")
                cell.grid_propagate(False)
                
                # Configure cell grid - top row takes all extra space
                cell.grid_rowconfigure(0, weight=1)  # Icon area expands
                cell.grid_rowconfigure(1, weight=0)  # Text area fixed
                cell.grid_columnconfigure(0, weight=1)  # Single centered column
                
                # Icon label - top-aligned and centered
                icon_label = ttk.Label(cell)
                icon_label.grid(row=0, sticky="n")  # "n" for top-aligned, centered horizontally
                
                # Text label - centered below icon
                text_label = ttk.Label(cell, anchor="center", wraplength=TEXT_WRAPLENGTH)
                text_label.grid(row=1, sticky="ew", pady=(0, 5))
                
                # Right-click menu
                cell.bind("<Button-3>", lambda e, r=row, c=col: self.show_context_menu(e, r, c))
                
                row_cells.append((cell, icon_label, text_label))
            self.cells.append(row_cells)
        
        # Pagination Frame
        pagination_frame = ttk.Frame(self.main_frame)
        pagination_frame.grid(row=2, column=0, sticky="", pady=10)
        
        inner_pagination = ttk.Frame(pagination_frame)
        inner_pagination.pack()
        
        self.prev_btn = ttk.Button(inner_pagination, text="← Prev", command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=PADX)
        
        self.page_label = ttk.Label(inner_pagination, text="Page 1")
        self.page_label.pack(side=tk.LEFT)
        
        self.next_btn = ttk.Button(inner_pagination, text="Next →", command=self.next_page)
        self.next_btn.pack(side=tk.LEFT, padx=PADX)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_bar.grid(row=3, column=0, sticky="ew")
    
    def show_context_menu(self, event, row, col):
        """Show edit menu on right-click"""
        try:
            cell, _, text_label = self.cells[row][col]
            icon_id = text_label.cget("text").split("\n")[0]
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit Metadata", command=lambda: self.edit_metadata(row, col))
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass
    
    def edit_metadata(self, row, col):
        """Edit metadata popup - enhanced version with category support"""
        try:
            _, _, text_label = self.cells[row][col]
            icon_id = text_label.cget("text").split("\n")[0]
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, category, keywords, metadata_json FROM ac_icons WHERE icon_id=?", (icon_id,))
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("Error", f"Icon {icon_id} not found in database")
                return
            
            name, category, keywords, metadata_json = result
            
            # Larger edit window
            edit_win = tk.Toplevel(self.root)
            edit_win.title(f"Edit {icon_id}")
            edit_win.geometry("450x350")  # Larger size for category field
            edit_win.minsize(400, 300)   # Minimum size
            
            # Main container
            main_frame = ttk.Frame(edit_win)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Form fields with labels
            ttk.Label(main_frame, text="Icon ID:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            ttk.Label(main_frame, text=icon_id).grid(row=0, column=1, sticky="w", padx=5, pady=5)
            
            ttk.Label(main_frame, text="Name:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            name_var = tk.StringVar(value=name or "")
            name_entry = ttk.Entry(main_frame, textvariable=name_var, width=35)
            name_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
            
            ttk.Label(main_frame, text="Category:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            category_var = tk.StringVar(value=category or "")
            category_entry = ttk.Entry(main_frame, textvariable=category_var, width=35)
            category_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
            
            ttk.Label(main_frame, text="Keywords:").grid(row=3, column=0, sticky="ne", padx=5, pady=5)
            keywords_var = tk.StringVar(value=keywords or "")
            keywords_entry = ttk.Entry(main_frame, textvariable=keywords_var, width=35)
            keywords_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
            
            # Metadata JSON in scrollable text widget
            ttk.Label(main_frame, text="Metadata JSON:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
            json_frame = ttk.Frame(main_frame)
            json_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)
            
            json_text = tk.Text(json_frame, wrap=tk.WORD, width=35, height=8)
            scrollbar = ttk.Scrollbar(json_frame, orient="vertical", command=json_text.yview)
            json_text.configure(yscrollcommand=scrollbar.set)
            
            json_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Load JSON data
            try:
                json_data = json.loads(metadata_json) if metadata_json else {}
                json_text.insert("1.0", json.dumps(json_data, indent=2))
            except:
                json_text.insert("1.0", metadata_json or "")
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=5, column=0, columnspan=2, pady=10)
            
            def save_changes():
                try:
                    # Update the database
                    cursor.execute("""
                        UPDATE ac_icons 
                        SET name=?, category=?, keywords=?
                        WHERE icon_id=?
                    """, (name_var.get() or None, 
                          category_var.get() or None,
                          keywords_var.get() or None,
                          icon_id))
                    conn.commit()
                    self.display_page()  # Refresh view
                    edit_win.destroy()
                    messagebox.showinfo("Success", "Metadata updated successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update: {str(e)}")
            
            ttk.Button(button_frame, text="Save", command=save_changes).pack(side="right", padx=5)
            ttk.Button(button_frame, text="Cancel", command=edit_win.destroy).pack(side="right", padx=5)
            
            # Configure grid weights
            main_frame.grid_rowconfigure(4, weight=1)
            main_frame.grid_columnconfigure(1, weight=1)
            
        except Exception as e:
            messagebox.showerror("Error", f"Couldn't edit: {str(e)}")
    
    def load_data(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ac_icons")
            self.total_icons = cursor.fetchone()[0]
            self.status_var.set(f"Loaded {self.total_icons} icons | {COLUMNS}×{ROWS} grid")
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            
    def display_page(self):
        for row in self.cells:
            for cell, icon_label, text_label in row:
                icon_label.config(image='')
                icon_label.image = None
                text_label.config(text='')
        
        if self.total_icons == 0:
            return
            
        total_pages = math.ceil(self.total_icons / (COLUMNS * ROWS))
        self.page_label.config(text=f"Page {self.current_page}/{total_pages}")
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < total_pages else tk.DISABLED)
        
        offset = (self.current_page - 1) * (COLUMNS * ROWS)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if self.search_var.get():
                query = """
                SELECT icon_id, name, category, icon_data FROM ac_icons 
                WHERE icon_id LIKE ? OR name LIKE ? OR category LIKE ? OR keywords LIKE ?
                LIMIT ? OFFSET ?
                """
                params = (f"%{self.search_var.get()}%", f"%{self.search_var.get()}%", 
                         f"%{self.search_var.get()}%", f"%{self.search_var.get()}%",
                         COLUMNS * ROWS, offset)
            else:
                query = "SELECT icon_id, name, category, icon_data FROM ac_icons LIMIT ? OFFSET ?"
                params = (COLUMNS * ROWS, offset)
                
            cursor.execute(query, params)
            items = cursor.fetchall()
            
            for idx, (icon_id, name, category, icon_data) in enumerate(items):
                row = idx // COLUMNS
                col = idx % COLUMNS
                
                if row >= ROWS:
                    break
                    
                cell, icon_label, text_label = self.cells[row][col]
                
                try:
                    img = Image.open(io.BytesIO(icon_data))
                    img.thumbnail((ICON_WIDTH, ICON_HEIGHT))
                    photo = ImageTk.PhotoImage(img)
                    icon_label.config(image=photo)
                    icon_label.image = photo
                except Exception:
                    icon_label.config(text="[Image]")
                
                # Enhanced text display with category
                text_parts = [icon_id]
                if name:
                    text_parts.append(name)
                if category:
                    text_parts.append(f"[{category}]")
                
                text_label.config(text="\n".join(text_parts))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load page: {str(e)}")
            
    def search_icons(self):
        search_term = self.search_var.get().strip()
        if not search_term:
            self.reset_search()
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM ac_icons 
                WHERE icon_id LIKE ? OR name LIKE ? OR category LIKE ? OR keywords LIKE ?
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            self.total_icons = cursor.fetchone()[0]
            self.current_page = 1
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
            
    def reset_search(self):
        self.search_var.set("")
        self.load_data()
        
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_page()
            
    def next_page(self):
        if self.current_page < math.ceil(self.total_icons / (COLUMNS * ROWS)):
            self.current_page += 1
            self.display_page()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedIconViewer(root)
    root.mainloop()