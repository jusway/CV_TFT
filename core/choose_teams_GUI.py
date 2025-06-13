import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from core.backend import BackEnd

class ChooseTeamsGUI:
    def __init__(self,backend,callback=None):
        # 准备数据
        self.teams_dict = backend.get_lineups()
        self.hero_dict = backend.get_imgs()
        self.callback = callback  # 用于返回数据的回调函数
        # 新窗口
        self.root = tk.Toplevel()
        self.root.title("阵容英雄展示器")
        self.root.geometry("1500x700")
        # 创建顶部框架
        top_frame = ttk.Frame(self.root, padding="20")
        top_frame.pack(fill=X)
        # 创建标签和下拉菜单
        ttk.Label(top_frame, text="选择阵容:").pack(side=LEFT, padx=5)
        self.team_var = StringVar()
        self.team_combobox = ttk.Combobox(
            top_frame,
            textvariable=self.team_var,
            values=list(self.teams_dict.keys()),
            state="readonly",
            width=80
        )
        self.team_combobox.pack(side=LEFT, padx=5)
        self.team_combobox.current(0)
        self.team_combobox.bind("<<ComboboxSelected>>", self.update_display)
        # 创建显示英雄的框架
        self.hero_frame = ttk.Frame(self.root, padding="20")
        self.hero_frame.pack(fill=BOTH, expand=True)
        # 创建底部按钮框架
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=X, side=BOTTOM)
        # 添加确定按钮
        confirm_btn = ttk.Button(
            button_frame,
            text="确定",
            command=self.confirm_selection,
            width=15
        )
        confirm_btn.pack(side=RIGHT, padx=10)
        # 添加取消按钮
        cancel_btn = ttk.Button(
            button_frame,
            text="取消",
            command=self.root.destroy,
            width=15
        )
        cancel_btn.pack(side=RIGHT)
        # 初始化显示
        self.current_photos = []  # 保存对PhotoImage对象的引用
        self.update_display()

    def update_display(self, event=None):
        # 清除当前显示
        for widget in self.hero_frame.winfo_children():
            widget.destroy()
        self.current_photos = []  # 清除旧引用

        # 获取选中的阵容
        selected_team = self.team_var.get()
        if not selected_team:
            return

        # 获取该阵容的英雄列表
        heroes = self.teams_dict.get(selected_team, [])
        if not heroes:
            ttk.Label(self.hero_frame, text="该阵容没有英雄数据").pack(pady=50)
            return

        # 创建英雄展示区
        container = ttk.Frame(self.hero_frame)
        container.pack(expand=True)

        # 每行显示4个英雄
        row, col = 0, 0
        max_cols = 4

        for hero in heroes:
            if hero not in self.hero_dict:
                continue

            # 转换PIL图像为Tkinter PhotoImage
            pil_img = self.hero_dict[hero]
            # 调整图像大小（可选）
            # pil_img = pil_img.resize((120, 120), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            self.current_photos.append(tk_img)  # 保存引用
            # 创建单个英雄的展示框架
            hero_card = ttk.Frame(container, padding=10)
            hero_card.grid(row=row, column=col, padx=15, pady=15)
            # 显示英雄图片
            label_img = ttk.Label(hero_card, image=tk_img)
            label_img.pack()
            # 显示英雄名字
            # label_name = ttk.Label(hero_card, text=hero, font=("Arial", 10, "bold"))
            # label_name.pack(pady=5)
            # 更新网格位置
            col = (col + 1) % max_cols
            if col == 0:
                row += 1

    def confirm_selection(self):
        """返回选择的阵容信息并关闭窗口"""
        selected_team = self.team_var.get()
        if selected_team and self.callback:
            # 获取阵容详细信息
            heroes = self.teams_dict.get(selected_team, [])
            # 返回给上级窗口
            self.callback({
                "team_name": selected_team,
                "heroes": heroes
            })
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    def handle_selection(selection):
        """处理返回的阵容信息"""
        print("选中的阵容:", selection["team_name"])
        print("包含英雄:", ", ".join(selection["heroes"]))


    backend = BackEnd()
    app = ChooseTeamsGUI(backend, callback=handle_selection)
    app.run()
