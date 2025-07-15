import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sqlite3
import re
import os

# フォント切り替え関数
def toggle_font_1():
    if font_checkbox_var_1.get():
        content_text.config(font=("Arial", 14))
        info_box.config(font=("Arial", 14))
        font_checkbox_var_2.set(False)  # Times New Romanのチェックを外す

def toggle_font_2():
    if font_checkbox_var_2.get():
        content_text.config(font=("Times New Roman", 14))
        info_box.config(font=("Times New Roman", 14))
        font_checkbox_var_1.set(False)  # Arialのチェックを外す

# グローバル変数で選ばれたデータベースのパスを保持
selected_db = None

# データベースを選ぶ関数（変更）
def choose_db():
    global selected_db  # グローバル変数を使用
    file_path = filedialog.askopenfilename(filetypes=[("Database", "*.db")])
    if file_path:
        selected_db = file_path  # 選択されたデータベースを保存

        # データベースファイル名を db_label に表示
        db_name = os.path.basename(selected_db)  # ファイルパスからファイル名を取得
        db_label.config(text=f"  {db_name}", font=("", 8))   # db_label に表示

# SQLiteから単語の意味を取得
def get_meaning(word):
    global selected_db
    if not selected_db:
        print("データベースが選ばれていません。")
        return None

    conn = sqlite3.connect(selected_db)  # 選ばれたデータベースを使用
    cursor = conn.cursor()
    cursor.execute("SELECT meaning, more_info FROM dictionary WHERE lower(word) = ?", (word.lower(),))
    result = cursor.fetchone()
    conn.close()

    if result:
        meaning, more_info = result
        return f"{word}\n{meaning}\n\n\n{more_info or ''}"  # MeaningとMore Infoのラベルを削除し、空白2行追加
    else:
        return f"{word}\nこの単語は登録されていません。"

selected_word = None
highlighted_tags = []
db_editor_window = None  # Edit DBウィンドウの参照を保持する変数

# 単語の意味を表示または消去
def toggle_word_info(event, word, tag):
    global selected_word

    if selected_word == word:
        clear_info()
    else:
        clear_highlight()

        info_text = get_meaning(word)
        info_box.config(state=tk.NORMAL)
        info_box.delete(1.0, tk.END)
        info_box.insert(tk.END, info_text)
        info_box.config(state=tk.DISABLED)

        content_text.tag_config(tag, background="yellow")
        selected_word = word

# クリアボタン処理
def clear_info():
    global selected_word
    clear_highlight()
    info_box.config(state=tk.NORMAL)
    info_box.delete(1.0, tk.END)
    info_box.config(state=tk.DISABLED)
    selected_word = None

# すべての単語の色を戻す
def clear_highlight():
    for tag in highlighted_tags:
        content_text.tag_config(tag, background="")

# 派生形から基底形を抽出する関数
def get_base_form(word, database_words):
    # 記号を削除
    word = re.sub(r"^\W+|\W+$", "", word)  # 先頭・末尾の記号を削除
    word = re.sub(r"'s\b", "", word)  # 'sを単語の一部と認識し削除

    # 基底形の候補を順次生成
    candidates = [word]  # 最初はそのままの単語を候補に追加

    # "ies" や "ied" で終わる単語に対する処理
    if word.endswith("ies") and len(word) > 3:
        candidates.append(word[:-3] + "y")  # 例: studies → study
    elif word.endswith("ied") and len(word) > 3:
        candidates.append(word[:-3] + "y")  # 例: studied → study
    # "es" の処理
    elif word.endswith("es") and len(word) > 3:
        candidates.append(word[:-2])  # 例: matches → match
        candidates.append(word[:-2] + "e")  # 例: expenses → expense

    elif word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        candidates.append(word[:-1])  # 例: messages → message, lines → line

    # 動詞の派生形「ing」の処理
    if word.endswith("ing") and len(word) > 4:
        base_form = word[:-3]  # まず「ing」を削除
        candidates.append(base_form)
        # 重複文字処理 (例: running → run)
        if len(base_form) > 1 and base_form[-1] == base_form[-2]:
            candidates.append(base_form[:-1])
        elif len(base_form) > 1:
            candidates.append(base_form + "e")  # 例: recharg → recharge

    # 過去形「ed」の処理
    if word.endswith("ed") and len(word) > 2:
        base_form = word[:-2]  # まず「ed」を削除
        candidates.append(base_form)
        # 重複文字処理 (例: planned → plan)
        if len(base_form) > 1 and base_form[-1] == base_form[-2]:
            candidates.append(base_form[:-1])
        elif len(base_form) > 1:
            candidates.append(word[:-1])  # 例: combined → combine

    # 最初の検索：候補がデータベースにあるか確認
    found = False
    for candidate in candidates:
        if candidate in database_words:
            found = True
            return candidate  # 見つかればその基底形を返す
            

    # 最初の検索で見つからなかった場合、再検索を実行
    if found == True:
        for candidate in candidates:
            if candidate in database_words:
                return candidate  # 2回目の検索で見つかればその基底形を返す
            
    # デバッグ出力: 候補を表示
    #print(f"Original word: {word}, Candidates: {candidates}")        

    # それでも見つからなければ、元の単語を返す
    return word  # 基底形が見つからなかった場合は元の単語を返す

# ハイライトの処理
def highlight_words():
    global highlighted_tags
    highlighted_tags.clear()  # リセット

    if not selected_db:
        print("データベースが選ばれていません。")
        return

    conn = sqlite3.connect(selected_db)  # 選ばれたデータベースを使用
    cursor = conn.cursor()
    cursor.execute("SELECT lower(word) FROM dictionary")  # データベースの単語を小文字化して取得
    words = [row[0] for row in cursor.fetchall()]
    conn.close()

    text_content = content_text.get("1.0", tk.END)

    for word in text_content.split():  # テキスト内の単語を1つずつ処理
        clean_word = re.sub(r"[^\w]", "", word)  # 単語についている記号をすべて削除

        base_form = get_base_form(clean_word.lower(), words)  # 基底形を取得

        if base_form in words:  # データベース内に基底形がある場合
            start_idx = "1.0"
            while True:
                # 単語の前後の記号と'sを削除
                search_word = re.sub(r"^\W+|\W+$", "", word)
                search_word = re.sub(r"'s\b", "", search_word)
                search_word_no_quotes = search_word.strip('"')

                # ケースインセンシティブ検索
                start_idx = content_text.search(search_word_no_quotes.lower(), start_idx, stopindex=tk.END, nocase=True)
                if not start_idx:
                    break

                # 実際に一致したテキストから end_idx を計算
                matched_text = content_text.get(start_idx, f"{start_idx} + {len(search_word_no_quotes)}c")
                end_idx = f"{start_idx}+{len(matched_text)}c"

                # 単語の前後に明確な境界（単語境界、区切り文字）を確認
                prev_char_idx = f"{start_idx} - 1c"
                next_char_idx = f"{end_idx}"

                prev_char = content_text.get(prev_char_idx, start_idx) if content_text.index(start_idx) != "1.0" else " "
                next_char = content_text.get(next_char_idx, f"{end_idx} + 1c")

                if (prev_char.isspace() or not prev_char.isalnum()) and (next_char.isspace() or not next_char.isalnum()):
                    tag = f"tag_{clean_word.lower()}_{start_idx.replace('.', '_')}"  # 小文字でユニークタグ
                    content_text.tag_add(tag, start_idx, end_idx)
                    content_text.tag_bind(tag, "<Button-1>", lambda e, w=base_form, t=tag: toggle_word_info(e, w, t))
                    highlighted_tags.append(tag)

                # 次の検索位置に移動
                start_idx = end_idx

# ファイル選択ダイアログを開いてテキストを読み込む
def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            text_data = f.read()
        content_text.config(state=tk.NORMAL)
        content_text.delete(1.0, tk.END)
        content_text.insert(tk.END, text_data)
        content_text.config(state=tk.DISABLED)
        highlight_words()
        file_name = os.path.basename(file_path)
        file_label.config(text=file_name, font=("Arial", 8))  # 読み込んだファイル名のフォントサイズを8に設定          


# データベース関連処理
def open_db_editor():
    global db_editor_window

    if db_editor_window is not None and tk.Toplevel.winfo_exists(db_editor_window):
        db_editor_window.focus()
        return

    db_editor_window = tk.Toplevel(root)
    db_editor_window.title("Dictionary DB Editor")
    db_editor_window.geometry("860x420")

    treeview = ttk.Treeview(db_editor_window, columns=("Word", "Meaning", "More Info"), show="headings", height=15)
    treeview.heading("Word", text="Word", command=lambda: sort_data("word"))
    treeview.heading("Meaning", text="Meaning")
    treeview.heading("More Info", text="More Info")

    treeview.column("Word", width=150, anchor="w")
    treeview.column("Meaning", width=200, anchor="w")
    treeview.column("More Info", width=200, anchor="w")

    scrollbar = tk.Scrollbar(db_editor_window, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    treeview.pack(fill=tk.BOTH, expand=True)

    def add_entry():
        new_word = entry_word.get().strip()
        new_meaning = entry_meaning.get().strip()
        new_more_info = entry_more_info.get().strip()
        if new_word and new_meaning:
            try:
                with sqlite3.connect(selected_db) as conn:  # 選ばれたデータベースを使用
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM dictionary WHERE lower(word) = ?", (new_word.lower(),))
                    if cursor.fetchone():
                        messagebox.showwarning("Duplicate Entry", f"'{new_word}' はすでに登録されています。")
                        return
                    cursor.execute("INSERT INTO dictionary (word, meaning, more_info) VALUES (?, ?, ?)",
                                   (new_word, new_meaning, new_more_info))
                    conn.commit()
                load_data()
                highlight_words()
                entry_word.delete(0, tk.END)
                entry_meaning.delete(0, tk.END)
                entry_more_info.delete(0, tk.END)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add entry: {e}")

    def edit_cell(event):
        selected_item = treeview.selection()
        if not selected_item:
            return
        column = treeview.identify_column(event.x)
        row = treeview.identify_row(event.y)
        if not row or column == "#0":
            return
        item_id = treeview.identify("item", event.x, event.y)
        column_id = column.replace("#", "")
        old_value = treeview.item(item_id, "values")[int(column_id) - 1]

        entry = tk.Entry(db_editor_window)
        entry.insert(0, old_value)
        entry.place(x=event.x, y=event.y)
        entry.focus()

        def on_entry_return(event):
            new_value = entry.get()
            entry.destroy()
            if new_value != old_value:
                with sqlite3.connect(selected_db) as conn:  # 選ばれたデータベースを使用
                    cursor = conn.cursor()
                    word_value = treeview.item(item_id, "values")[0]
                    if column_id == "1":
                        cursor.execute("UPDATE dictionary SET word = ? WHERE word = ?", (new_value, old_value))
                    elif column_id == "2":
                        cursor.execute("UPDATE dictionary SET meaning = ? WHERE word = ?", (new_value, word_value))
                    elif column_id == "3":
                        cursor.execute("UPDATE dictionary SET more_info = ? WHERE word = ?", (new_value, word_value))
                    conn.commit()
                load_data()

        entry.bind("<Return>", on_entry_return)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def delete_entry():
        selected_item = treeview.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a word to delete.")
            return
        selected_word = treeview.item(selected_item, "values")[0]
        try:
            with sqlite3.connect(selected_db) as conn:  # 選ばれたデータベースを使用
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dictionary WHERE word = ?", (selected_word,))
                conn.commit()
            load_data()
            highlight_words()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to delete {selected_word}: {e}")

    def sort_data(column):
        try:
            with sqlite3.connect(selected_db) as conn:  # 選ばれたデータベースを使用
                cursor = conn.cursor()
                cursor.execute(f"SELECT word, meaning, more_info FROM dictionary ORDER BY {column} ASC")
                rows = cursor.fetchall()
            treeview.delete(*treeview.get_children())
            for row in rows:
                treeview.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to sort data: {e}")

    def search_entry():
        search_word = search_box.get().strip().lower()
        if not search_word:
            messagebox.showwarning("Warning", "Please enter a word to search.")
            return
        for item in treeview.get_children():
            word = treeview.item(item, "values")[0].lower()
            if word == search_word:
                treeview.selection_set(item)
                treeview.see(item)
                return
        messagebox.showinfo("Info", f"No matching word found for '{search_word}'.")

    def load_data():
        try:
            with sqlite3.connect(selected_db) as conn:  # 選ばれたデータベースを使用
                cursor = conn.cursor()
                cursor.execute("SELECT word, meaning, more_info FROM dictionary")
                rows = cursor.fetchall()
            treeview.delete(*treeview.get_children())
            for row in rows:
                treeview.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    # UIパーツのセットアップ
    search_frame = tk.Frame(db_editor_window)
    search_frame.pack(fill=tk.X, pady=5)
    tk.Label(search_frame, text="Search Word:", font=("Courier New", 12)).pack(side=tk.LEFT, padx=5)
    search_box = tk.Entry(search_frame, width=20)
    search_box.pack(side=tk.LEFT, padx=5)
    tk.Button(search_frame, text="Search", command=search_entry).pack(side=tk.LEFT, padx=5)

    entry_frame = tk.Frame(db_editor_window)
    entry_frame.pack(fill=tk.X, pady=5)
    tk.Label(entry_frame, text="Word:", font=("Courier New", 12)).grid(row=0, column=0, padx=5)
    entry_word = tk.Entry(entry_frame, width=20)
    entry_word.grid(row=0, column=1, padx=5)
    tk.Label(entry_frame, text="Meaning:", font=("Courier New", 12)).grid(row=0, column=2, padx=5)
    entry_meaning = tk.Entry(entry_frame, width=30)
    entry_meaning.grid(row=0, column=3, padx=5)
    tk.Label(entry_frame, text="More Info:", font=("Courier New", 12)).grid(row=0, column=4, padx=5)
    entry_more_info = tk.Entry(entry_frame, width=30)
    entry_more_info.grid(row=0, column=5, padx=5)
    tk.Button(entry_frame, text="Add", command=add_entry).grid(row=0, column=6, padx=5)

    delete_button = tk.Button(db_editor_window, text="Delete", fg="red", command=delete_entry)
    delete_button.place(x=5, y=3)

    treeview.bind("<Double-1>", edit_cell)
    load_data()


# メインウィンドウの設定
root = tk.Tk()
root.title("最初にデータベースを読み込む")
root.geometry("1000x600")

# ボタンフレーム
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# 新しく db_label を追加（データベース用）
db_label = tk.Label(button_frame, text="", font=("Arial", 12))
db_label.pack(side=tk.LEFT, padx=10)

# ファイルパスを表示するラベルを配置
file_label = tk.Label(button_frame, text="", font=("Arial", 12))
file_label.pack(side=tk.LEFT, padx=10)

choose_button = tk.Button(button_frame, text="Choose DB", font=("Arial", 12), command=choose_db)
choose_button.pack(side=tk.LEFT, padx=10)

open_button = tk.Button(button_frame, text="Open Text File", font=("Arial", 12), command=open_file)
open_button.pack(side=tk.LEFT, padx=10)

db_edit_button = tk.Button(button_frame, text="Edit DB", font=("Arial", 12), command=open_db_editor)
db_edit_button.pack(side=tk.LEFT, padx=10)

clear_button = tk.Button(button_frame, text="Clear", font=("Arial", 12), command=clear_info)
clear_button.pack(side=tk.LEFT, padx=10)

# フォントチェックボックスの状態を制御する関数
def toggle_font(font_type):
    if font_type == "Arial":
        font_checkbox_var_2.set(False)  # Times New Roman をオフにする
    elif font_type == "Times New Roman":
        font_checkbox_var_1.set(False)  # Arial をオフにする

# フォント切り替えのチェックボックス
font_checkbox_var_1 = tk.BooleanVar(value=True)  # Arialをデフォルトに
font_checkbox_var_2 = tk.BooleanVar(value=False)  # Times New RomanはFalse

font_frame = tk.Frame(root)
font_frame.pack(pady=10)

checkbox_1 = tk.Checkbutton(font_frame, text="Arial", variable=font_checkbox_var_1, command=lambda: toggle_font("Arial"))
checkbox_1.pack(side=tk.LEFT, padx=10)

checkbox_2 = tk.Checkbutton(font_frame, text="Times New Roman", variable=font_checkbox_var_2, command=lambda: toggle_font("Times New Roman"))
checkbox_2.pack(side=tk.LEFT, padx=10)

# フォントサイズ変更用の変数
font_size_var = tk.StringVar(value="14")  # デフォルト値を文字列で管理

# フォントサイズ変更のエントリー（数値入力欄）
font_size_entry = tk.Entry(font_frame, textvariable=font_size_var, width=5)
font_size_entry.pack(side=tk.LEFT, padx=10)

# フォント適用ボタン
apply_font_button = tk.Button(font_frame, text="適用", command=lambda: update_font_settings())
apply_font_button.pack(side=tk.LEFT, padx=10)

# フォント設定を適用する関数
def update_font_settings():
    # フォントサイズの取得（入力されていない場合は変更しない）
    new_size_str = font_size_var.get().strip()
    if not new_size_str:
        return  # 入力なしなら処理をしない

    try:
        new_size = int(new_size_str)
    except ValueError:
        return  # 数値以外が入力されていた場合も何もしない

    # チェックボックスの状態に応じてフォント種類を決定
    font_family = "Arial" if font_checkbox_var_1.get() else "Times New Roman"

    # フォントサイズと種類を適用
    content_text.config(font=(font_family, new_size))
    info_box.config(font=(font_family, new_size)) #←フォントサイズの変更を下画面にも適用する場合オン

# PanedWindow（上下の比率変更可能）
paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=10)
paned_window.pack(fill=tk.BOTH, expand=True)

# 上側のテキスト表示エリアとスクロールバー
content_frame = tk.Frame(paned_window)
content_scrollbar = tk.Scrollbar(content_frame, orient=tk.VERTICAL)
content_text = tk.Text(content_frame, wrap=tk.WORD, font=("Arial", 14), height=15, yscrollcommand=content_scrollbar.set)
content_scrollbar.config(command=content_text.yview)

content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
paned_window.add(content_frame)

# 下側の意味表示エリアとスクロールバー
info_frame = tk.Frame(paned_window)
info_scrollbar = tk.Scrollbar(info_frame, orient=tk.VERTICAL)
info_box = tk.Text(info_frame, wrap=tk.WORD, font=("Arial", 14), height=15, bg="#f4f4f4", yscrollcommand=info_scrollbar.set)
info_scrollbar.config(command=info_box.yview)

info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
paned_window.add(info_frame)

root.mainloop()