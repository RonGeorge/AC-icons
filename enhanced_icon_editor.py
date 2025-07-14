import sqlite3
from PIL import Image, ImageTk
import io
import tkinter as tk
from tkinter import ttk, messagebox
import json

DB_PATH = "enhanced_icons.db"
ICON_SIZE = 32
WINDOW_TITLE = "Enhanced Asheron's Call Icon Database Editor"
BG_COLOR = "#f0f0f0"
FONT_COLOR = "#000000"
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 9
COLUMN_WIDTHS = {
    'icon': 50,
    'icon_id': 80,
    'name': 150,
    'category': 120,
    'keywords': 300,
    'metadata': 300
}
PAGE_SIZE = 100

KEYWORDS_POPUP_WIDTH = 60
KEYWORDS_POPUP_HEIGHT = 20

class EnhancedIconDatabaseEditor:
    def __init__(self, root):
        self.root = root
        self.current_data = []
        self.image_references = []
        self.current_page = 0
        self.dark_mode = False

        self.root.title(WINDOW_TITLE)
        self.root.geometry("1200x600")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(700, 400)

        self.setup_styles()
        self.setup_ui()
        self.load_data()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Dark.Treeview",
            font=(FONT_FAMILY, FONT_SIZE),
            rowheight=ICON_SIZE + 4,
            background=BG_COLOR,
            fieldbackground=BG_COLOR,
            foreground=FONT_COLOR
        )
        style.configure("Treeview.Heading", font=(FONT_FAMILY, FONT_SIZE, 'bold'))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FONT_COLOR)
        style.configure("TButton", background=BG_COLOR, foreground=FONT_COLOR)
        style.configure("TEntry", fieldbackground=BG_COLOR, foreground=FONT_COLOR)

        style.map("Treeview", background=[('selected', '#607080')])

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
            selectmode="browse",
            style="Dark.Treeview"
        )

        self.tree.column("#0", width=COLUMN_WIDTHS['icon'], anchor="center")
        self.tree.heading("#0", text="Icon")
        for col, width in COLUMN_WIDTHS.items():
            if col == 'icon': continue
            self.tree.column(col, width=width, anchor="w")
            self.tree.heading(col, text=col.replace('_', ' ').title())

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
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
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=tk.X)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        global BG_COLOR, FONT_COLOR
        if self.dark_mode:
            BG_COLOR, FONT_COLOR, viewer_bg = "#1e1e1e", "#dcdcdc", "#2e2e2e"
            self.dark_mode_btn.config(text="Light Mode")
        else:
            BG_COLOR, FONT_COLOR, viewer_bg = "#f0f0f0", "#000000", BG_COLOR
            self.dark_mode_btn.config(text="Dark Mode")
        self.root.configure(bg=BG_COLOR)
        self.setup_styles()

        def apply_colors(widget):
            # Skip direct styling for Treeview widgets (styled via ttk.Style)
            if isinstance(widget, ttk.Treeview):
                return
            # Text widgets get dedicated background
            if isinstance(widget, tk.Text):
                widget.configure(background=viewer_bg, foreground=FONT_COLOR)
                return

            opts = widget.configure()
            if 'background' in opts:
                try:
                    widget.configure(background=BG_COLOR)
                except tk.TclError:
                    pass
            if 'foreground' in opts:
                try:
                    widget.configure(foreground=FONT_COLOR)
                except tk.TclError:
                    pass
            for c in widget.winfo_children():
                apply_colors(c)

        apply_colors(self.root)

    def reset_search(self):
        self.search_var.set("")
        self.current_page = 0
        self.load_data()

    def search_icons(self):
        self.current_page = 0
        term = self.search_var.get().strip()
        self.load_data(term if term else None)

    def load_data(self, search_term=None):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            if search_term:
                q = ("SELECT icon_id,name,category,keywords,metadata_json,icon_data FROM ac_icons "
                     "WHERE icon_id LIKE ? OR name LIKE ? OR category LIKE ? OR keywords LIKE ? "
                     "ORDER BY icon_id")
                params = (f"%{search_term}%",)*4
                cur.execute(q, params)
            else:
                cur.execute("SELECT icon_id,name,category,keywords,metadata_json,icon_data FROM ac_icons ORDER BY icon_id")
            self.current_data = cur.fetchall()
            conn.close()
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

    def display_page(self):
        self.tree.delete(*self.tree.get_children())
        self.image_references = []
        start, end = self.current_page*PAGE_SIZE, (self.current_page+1)*PAGE_SIZE
        for icon_id,name,cat,kw,meta,imgdata in self.current_data[start:end]:
            try:
                img = Image.open(io.BytesIO(imgdata))
                img.thumbnail((ICON_SIZE, ICON_SIZE))
                photo = ImageTk.PhotoImage(img)
                self.image_references.append(photo)
            except: photo=None
            self.tree.insert("", "end", image=photo, values=(icon_id,name,cat,kw,"[...] Click to view"))
        total = max(1, (len(self.current_data)+PAGE_SIZE-1)//PAGE_SIZE)
        self.page_label.config(text=f"Page {self.current_page+1} of {total}")
        self.status_var.set(f"Showing {min(len(self.current_data)-start, PAGE_SIZE)} of {len(self.current_data)} icons")

    def next_page(self):
        if (self.current_page+1)*PAGE_SIZE < len(self.current_data):
            self.current_page+=1; self.display_page()

    def prev_page(self):
        if self.current_page>0:
            self.current_page-=1; self.display_page()

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item: return
        idx = int(col.replace('#',''))-1
        cols=list(COLUMN_WIDTHS.keys())[1:]
        if idx<0 or idx>=len(cols): return
        col_name=cols[idx]
        icon_id=self.tree.set(item, '#1')
        if col_name=='metadata':
            conn=sqlite3.connect(DB_PATH);cur=conn.cursor()
            cur.execute("SELECT metadata_json FROM ac_icons WHERE icon_id=?", (icon_id,))
            row=cur.fetchone();conn.close()
            current=json.dumps(json.loads(row[0]), indent=2) if row else ""
        else:
            current=self.tree.set(item, f"#{idx+1}")
        win=tk.Toplevel(self.root)
        win.title(f"Edit {col_name.replace('_',' ')}")
        if col_name in ['metadata','keywords']:
            frm=ttk.Frame(win);frm.pack(fill=tk.BOTH,expand=True,padx=5,pady=5)
            txt=tk.Text(frm,wrap=tk.WORD,width=KEYWORDS_POPUP_WIDTH,height=KEYWORDS_POPUP_HEIGHT if col_name=='keywords' else 20)
            sb=ttk.Scrollbar(frm,orient=tk.VERTICAL,command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side=tk.LEFT,fill=tk.BOTH,expand=True);sb.pack(side=tk.RIGHT,fill=tk.Y)
            txt.insert("1.0",current)
        else:
            ent=ttk.Entry(win,width=50);ent.pack(padx=5,pady=5);ent.insert(0,current);ent.select_range(0,tk.END);ent.focus()
        def save():
            new=txt.get("1.0","end-1c") if col_name in ['metadata','keywords'] else ent.get()
            if col_name=='metadata':
                try: json.loads(new)
                except json.JSONDecodeError: messagebox.showerror("Error","Invalid JSON");return
            self.tree.set(item, f"#{idx+1}", "[...] Click to view" if col_name=='metadata' else new)
            conn=sqlite3.connect(DB_PATH);cur=conn.cursor()
            if col_name=='name': cur.execute("UPDATE ac_icons SET name=? WHERE icon_id=?", (new,icon_id))
            if col_name=='category': cur.execute("UPDATE ac_icons SET category=? WHERE icon_id=?", (new,icon_id))
            if col_name=='keywords': cur.execute("UPDATE ac_icons SET keywords=? WHERE icon_id=?", (new,icon_id))
            if col_name=='metadata': cur.execute("UPDATE ac_icons SET metadata_json=? WHERE icon_id=?", (new,icon_id))
            conn.commit();conn.close();win.destroy()
        ttk.Button(win,text="Save",command=save).pack(pady=5)

if __name__ == "__main__":
    root=tk.Tk()
    app=EnhancedIconDatabaseEditor(root)
    root.mainloop()
