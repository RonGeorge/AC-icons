import sqlite3
from PIL import Image, ImageTk
import io
import tkinter as tk
from tkinter import ttk, messagebox
import json

DB_PATH = "C:/GitHub/AC-icons/acicons.db"
ICON_SIZE = 32
WINDOW_TITLE = "Demonic Icon Database Editor"
BG_COLOR = "#f0f0f0"
FONT_COLOR = "#000000"
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 9
COLUMN_WIDTHS = {
    'icon': 50,
    'icon_id': 80,
    'name': 150,
    'keywords': 300,
    'metadata': 300
}
PAGE_SIZE = 100

KEYWORDS_POPUP_WIDTH = 60
KEYWORDS_POPUP_HEIGHT = 20

class IconDatabaseEditor:
    def __init__(self, root):
        self.root = root
        self.current_data = []
        self.image_references = []
        self.current_page = 0
        self.dark_mode = False

        self.root.title(WINDOW_TITLE)
        self.root.geometry("1000x600")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(600, 400)

        self.setup_styles()
        self.setup_ui()
        self.load_data()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=(FONT_FAMILY, FONT_SIZE), rowheight=ICON_SIZE + 4)
        style.configure("Treeview.Heading", font=(FONT_FAMILY, FONT_SIZE, 'bold'))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FONT_COLOR)
        style.configure("TButton", background=BG_COLOR, foreground=FONT_COLOR)
        style.configure("TEntry", fieldbackground=BG_COLOR, foreground=FONT_COLOR)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X)

        self.dark_mode_btn = ttk.Button(top_bar, text="Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_btn.pack(side=tk.RIGHT)

        search_frame = ttk.Frame(top_bar)
        search_frame.pack(fill=tk.X, pady=5, expand=True)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self.search_icons())

        ttk.Button(search_frame, text="Search", command=self.search_icons).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=list(COLUMN_WIDTHS.keys())[1:],
            show="tree headings",
            selectmode="browse"
        )

        self.tree.column("#0", width=COLUMN_WIDTHS['icon'], anchor="center")
        self.tree.heading("#0", text="Icon")

        for col, width in COLUMN_WIDTHS.items():
            if col == 'icon':
                continue
            self.tree.column(col, width=width, anchor="w")
            self.tree.heading(col, text=col.replace('_', ' ').title())

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)

        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        status_bar.pack(fill=tk.X)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        global BG_COLOR, FONT_COLOR
        if self.dark_mode:
            BG_COLOR = "#1e1e1e"
            FONT_COLOR = "#dcdcdc"
            self.dark_mode_btn.config(text="Light Mode")
        else:
            BG_COLOR = "#f0f0f0"
            FONT_COLOR = "#000000"
            self.dark_mode_btn.config(text="Dark Mode")

        self.root.configure(bg=BG_COLOR)
        self.setup_styles()
        for widget in self.root.winfo_children():
            widget.configure(bg=BG_COLOR)

    def reset_search(self):
        self.search_var.set("")
        self.current_page = 0
        self.load_data()

    def search_icons(self):
        self.current_page = 0
        self.load_data(self.search_var.get().strip())

    def load_data(self, search_term=None):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if search_term:
                query = """
                    SELECT icon_id, name, keywords, metadata_json, icon_data 
                    FROM ac_icons 
                    WHERE icon_id LIKE ? OR name LIKE ? OR keywords LIKE ?
                    ORDER BY icon_id
                """
                params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
            else:
                query = "SELECT icon_id, name, keywords, metadata_json, icon_data FROM ac_icons ORDER BY icon_id"
                params = ()

            cursor.execute(query, params)
            self.current_data = cursor.fetchall()
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")

    def display_page(self):
        self.tree.delete(*self.tree.get_children())
        self.image_references = []

        start = self.current_page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_data = self.current_data[start:end]

        for icon_id, name, keywords, metadata_json, icon_data in page_data:
            try:
                img = Image.open(io.BytesIO(icon_data))
                img.thumbnail((ICON_SIZE, ICON_SIZE))
                photo = ImageTk.PhotoImage(img)
                self.image_references.append(photo)
            except:
                photo = None

            values = (icon_id, name, keywords, "[...] Click to view")
            self.tree.insert("", "end", text="", image=photo, values=values)

        total_pages = max(1, (len(self.current_data) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(text=f"Page {self.current_page + 1} of {total_pages}")
        self.status_var.set(f"Showing {len(page_data)} of {len(self.current_data)} icons")

    def next_page(self):
        if (self.current_page + 1) * PAGE_SIZE < len(self.current_data):
            self.current_page += 1
            self.display_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return

        col_id = int(col.replace('#', '')) - 1
        columns = list(COLUMN_WIDTHS.keys())[1:]
        if col_id >= len(columns):
            return

        col_name = columns[col_id]
        icon_id = self.tree.set(item, "#1")

        if col_name == "metadata":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT metadata_json FROM ac_icons WHERE icon_id=?", (icon_id,))
            row = cursor.fetchone()
            current_value = json.dumps(json.loads(row[0]), indent=2) if row and row[0] else ""
        else:
            current_value = self.tree.set(item, f"#{col_id + 1}")

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit {col_name.replace('_', ' ')}")

        if col_name in ["metadata", "keywords"]:
            text_frame = ttk.Frame(edit_win)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            height = KEYWORDS_POPUP_HEIGHT if col_name == "keywords" else 20

            text = tk.Text(text_frame, wrap=tk.WORD, width=KEYWORDS_POPUP_WIDTH, height=height)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)

            text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            text.insert("1.0", current_value)
        else:
            entry = ttk.Entry(edit_win, width=50)
            entry.pack(padx=5, pady=5)
            entry.insert(0, current_value)
            entry.select_range(0, tk.END)
            entry.focus()

        def save_changes():
            try:
                new_value = text.get("1.0", "end-1c") if col_name in ["metadata", "keywords"] else entry.get()
                if col_name == "metadata":
                    try:
                        json.loads(new_value)
                    except json.JSONDecodeError:
                        messagebox.showerror("Error", "Invalid JSON format")
                        return

                self.tree.set(item, f"#{col_id + 1}", "[...] Click to view" if col_name == "metadata" else new_value)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                if col_name == "name":
                    cursor.execute("UPDATE ac_icons SET name=? WHERE icon_id=?", (new_value, icon_id))
                elif col_name == "keywords":
                    cursor.execute("UPDATE ac_icons SET keywords=? WHERE icon_id=?", (new_value, icon_id))
                elif col_name == "metadata":
                    cursor.execute("UPDATE ac_icons SET metadata_json=? WHERE icon_id=?", (new_value, icon_id))

                conn.commit()
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {str(e)}")

        ttk.Button(edit_win, text="Save", command=save_changes).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = IconDatabaseEditor(root)
    root.mainloop()
