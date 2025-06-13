import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import dxcam
import pyautogui
from pynput import keyboard
from core.backend import BackEnd
from core.choose_teams_GUI import ChooseTeamsGUI
from core.config import Config
from PIL import Image, ImageTk


class AutoPickerGUI:

    def __init__(self, backend):
        # 初始化window - 增大窗口尺寸
        self.root = tk.Tk()
        self.root.title('云顶自动拿牌')
        self.root.geometry('1200x1000')  # 增大窗口尺寸

        # 设置字体
        self.large_font = ('微软雅黑', 14)  # 增大字体
        self.title_font = ('微软雅黑', 16, 'bold')  # 标题字体

        # 后端
        self.backend = backend
        # 截图器
        self.grab = dxcam.create(output_idx=Config.output_idx, output_color='RGB')
        # 当前数据
        self.team_name = '尚未选择阵容'
        self.heros = []
        self.hero_images = []  # 存储英雄图片的引用

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 添加标题
        title_label = ttk.Label(
            main_frame,
            text="云顶之弈自动拿牌工具",
            font=self.title_font
        )
        title_label.pack(pady=(0, 20))

        # 添加选择阵容按钮 - 增大按钮尺寸
        self.select_btn = ttk.Button(
            main_frame,
            text="选择阵容",
            command=self.open_team_selector,
            width=30
        )
        self.select_btn.pack(pady=10)

        # 添加按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # 添加删除英雄按钮
        self.delete_btn = ttk.Button(
            button_frame,
            text="删除英雄",
            command=self.open_delete_hero,
            width=15
        )
        self.delete_btn.pack(side=tk.LEFT, padx=10)

        # 添加增加英雄按钮
        self.add_btn = ttk.Button(
            button_frame,
            text="增加英雄",
            command=self.open_add_hero,
            width=15
        )
        self.add_btn.pack(side=tk.LEFT, padx=10)

        # 添加英雄图片展示区
        self.hero_images_frame = ttk.Frame(main_frame)
        self.hero_images_frame.pack(fill=tk.X, pady=10)

        # 添加英雄图片标题
        hero_title = ttk.Label(
            self.hero_images_frame,
            text="当前追踪英雄:",
            font=self.large_font
        )
        hero_title.pack(anchor=tk.W, padx=10, pady=(0, 5))

        # 添加英雄图片容器
        self.hero_images_container = ttk.Frame(self.hero_images_frame)
        self.hero_images_container.pack(fill=tk.X, padx=10, pady=5)

        # 初始占位文本
        self.placeholder_label = ttk.Label(
            self.hero_images_container,
            text="尚未选择英雄",
            font=self.large_font,
            foreground="gray"
        )
        self.placeholder_label.pack(pady=10)

        # 添加信息框框架
        info_frame = ttk.LabelFrame(main_frame, text="当前信息", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 减小信息框高度
        self.info_box = scrolledtext.ScrolledText(
            info_frame,
            width=90,
            height=10,  # 高度减半
            font=self.large_font,
            wrap=tk.WORD
        )
        self.info_box.pack(fill=tk.BOTH, expand=True)
        self.info_box.insert(tk.END, self.info_show())
        self.info_box.see(tk.END)
        self.info_box.config(state=tk.DISABLED)

        # 添加状态栏
        self.status_var = tk.StringVar(value="就绪 - 按 'n' 键开始自动选牌")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=self.large_font
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # 键盘监听
        self.listener = keyboard.Listener(on_press=self.on_press_n)
        self.listener.daemon = True
        self.listener.start()
        self.hero_lock = threading.Lock()

    def open_team_selector(self):
        """打开阵容选择窗口"""
        ChooseTeamsGUI(self.backend, self.callback)
        self.select_btn.config(state=tk.DISABLED)
        self.root.after(100, self.check_selector_closed)

    def open_delete_hero(self):
        """打开删除英雄窗口"""
        if not self.heros:
            messagebox.showinfo("提示", "当前没有英雄可删除")
            return
        DeleteHeroWindow(self.root, self.heros, self.backend.imgs_dict, self.update_hero_list)

    def open_add_hero(self):
        """打开增加英雄窗口"""
        AddHeroWindow(self.root, self.backend.imgs_dict, self.add_new_hero)

    def check_selector_closed(self):
        self.select_btn.config(state=tk.NORMAL)

    def info_show(self):
        res = f"当前阵容: {self.team_name}\n\n"
        res += "目标英雄:\n"
        for id, item in enumerate(self.heros):
            res += f"{id + 1}. {item}\n"
        res += "\n" + "*" * 70 + "\n\n"
        res += "按 'n' 键开始自动选牌\n"
        return res

    def callback(self, select_dict):
        """接收选择的阵容数据"""
        self.team_name = select_dict["team_name"]
        self.heros = select_dict["heroes"]
        self.update_hero_list(self.heros)

    def update_hero_list(self, new_heroes):
        """更新英雄列表并刷新界面"""
        self.heros = new_heroes

        # 更新信息框
        self.info_box.config(state=tk.NORMAL)
        self.info_box.delete(1.0, tk.END)
        self.info_box.insert(tk.END, self.info_show())
        self.info_box.see(tk.END)
        self.info_box.config(state=tk.DISABLED)

        # 更新英雄图片展示区
        self.update_hero_images()

        # 启用按钮
        self.select_btn.config(state=tk.NORMAL)
        self.status_var.set(f"已选择阵容: {self.team_name} - 按 'n' 键开始自动选牌")

    def add_new_hero(self, new_hero):
        """增加新英雄到列表"""
        if new_hero in self.heros:
            messagebox.showinfo("提示", f"英雄 {new_hero} 已在列表中")
            return

        self.heros.append(new_hero)
        self.update_hero_list(self.heros)
        messagebox.showinfo("成功", f"已添加英雄: {new_hero}")

    def update_hero_images(self):
        """更新英雄图片展示区 - 以两行显示，每行5个"""
        # 清除现有内容
        for widget in self.hero_images_container.winfo_children():
            widget.destroy()

        # 清除图片引用
        self.hero_images = []

        if not self.heros:
            # 如果没有英雄，显示占位文本
            self.placeholder_label = ttk.Label(
                self.hero_images_container,
                text="尚未选择英雄",
                font=self.large_font,
                foreground="gray"
            )
            self.placeholder_label.pack(pady=10)
            return

        # 创建第一行框架
        row1_frame = ttk.Frame(self.hero_images_container)
        row1_frame.pack(fill=tk.X, pady=5)

        # 创建第二行框架
        row2_frame = ttk.Frame(self.hero_images_container)
        row2_frame.pack(fill=tk.X, pady=5)

        # 为每个英雄创建图片标签
        for idx, hero in enumerate(self.heros[:10]):  # 最多显示10个英雄
            # 选择行框架
            row_frame = row1_frame if idx < 5 else row2_frame

            if hero in self.backend.imgs_dict:
                # 创建容器框架
                hero_frame = ttk.Frame(row_frame)
                hero_frame.pack(side=tk.LEFT, padx=5, pady=5)

                # 获取并转换图片
                pil_img = self.backend.imgs_dict[hero]
                tk_img = ImageTk.PhotoImage(pil_img)
                self.hero_images.append(tk_img)  # 保留引用

                # 创建图片标签
                img_label = ttk.Label(hero_frame, image=tk_img)
                img_label.pack()

                # 创建英雄名称标签
                name_label = ttk.Label(hero_frame, text=hero, font=('微软雅黑', 10))
                name_label.pack(pady=(5, 0))
            else:
                # 如果没有找到图片，显示文字
                hero_frame = ttk.Frame(row_frame)
                hero_frame.pack(side=tk.LEFT, padx=5, pady=5)

                name_label = ttk.Label(hero_frame, text=hero, font=('微软雅黑', 10))
                name_label.pack(pady=5)

        # 如果英雄数量超过10个，显示提示信息
        if len(self.heros) > 10:
            info_label = ttk.Label(
                self.hero_images_container,
                text=f"只显示前10个英雄（共{len(self.heros)}个）",
                font=('微软雅黑', 10),
                foreground="orange"
            )
            info_label.pack(pady=(10, 0))

    def on_press_n(self, key):
        try:
            if key.char == 'n' and self.heros:
                self.status_var.set("正在识别英雄...")
                sub_imgs = self.get_imgs()

                self.info_box.config(state=tk.NORMAL)
                self.info_box.insert(tk.END, "\n\n本次识别结果:\n\n")

                for i, img in enumerate(sub_imgs):
                    hero_name, score = self.backend.match(img)
                    self.info_box.insert(tk.END, f'位置 {i + 1}: {hero_name} ({round(score.item(), 2)})\n')
                    if hero_name in self.heros:
                        self.click(i, hero_name)

                self.info_box.see(tk.END)
                self.info_box.config(state=tk.DISABLED)
                self.status_var.set("识别完成 - 按 'n' 键再n次识别")
        except AttributeError:
            pass

    def click(self, idx, name):
        x, y = Config.point
        pyautogui.moveTo(x + 50 + idx * Config.move, y + 50 + Config.y_bias, duration=0)
        for _ in range(2):
            pyautogui.mouseDown(button="left")
            pyautogui.mouseUp(button="left")

        self.info_box.config(state=tk.NORMAL)
        self.info_box.insert(tk.END, f'[动作] 已选择: {name} (位置 {idx + 1})\n\n')
        self.info_box.see(tk.END)
        self.info_box.config(state=tk.DISABLED)
        self.status_var.set(f"已选择英雄: {name}")

    def get_imgs(self):
        img = None
        while img is None:
            img = self.grab.grab()
        sub_imgs = []
        x, y = Config.point
        for _ in range(5):
            sub_imgs.append(img[y:y + Config.h,
                            x:x + Config.w, :])
            x += Config.move
        return sub_imgs

    def run(self):
        self.root.mainloop()


class DeleteHeroWindow:
    """删除英雄窗口类"""

    def __init__(self, parent, heroes, imgs_dict, callback):
        self.parent = parent
        self.heroes = heroes
        self.imgs_dict = imgs_dict
        self.callback = callback

        # 创建二级窗口
        self.window = tk.Toplevel(parent)
        self.window.title("删除英雄")
        self.window.geometry("600x500")
        self.window.grab_set()  # 模态窗口

        # 标题
        title_label = ttk.Label(
            self.window,
            text="选择要删除的英雄",
            font=('微软雅黑', 14, 'bold')
        )
        title_label.pack(pady=10)

        # 说明文本
        info_label = ttk.Label(
            self.window,
            text="勾选要删除的英雄，然后点击确认删除",
            font=('微软雅黑', 10)
        )
        info_label.pack(pady=5)

        # 创建滚动框架
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 存储选择状态的变量
        self.selected_heroes = {hero: tk.BooleanVar(value=False) for hero in self.heroes}

        # 创建英雄选择框
        self.hero_frames = []
        for hero in self.heroes:
            frame = ttk.Frame(self.scrollable_frame, padding=5)
            frame.pack(fill=tk.X, padx=10, pady=5)
            self.hero_frames.append(frame)

            # 创建复选框
            chk = ttk.Checkbutton(frame, text=hero, variable=self.selected_heroes[hero])
            chk.pack(side=tk.LEFT, padx=5)

            # 显示英雄图片（如果有）
            if hero in self.imgs_dict:
                pil_img = self.imgs_dict[hero]
                # 调整图片大小
                pil_img = pil_img.resize((40, 40), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                img_label = ttk.Label(frame, image=tk_img)
                img_label.image = tk_img  # 保持引用
                img_label.pack(side=tk.LEFT, padx=5)

        # 按钮框架
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)

        # 确认按钮
        confirm_btn = ttk.Button(
            btn_frame,
            text="确认删除",
            command=self.delete_selected,
            width=15
        )
        confirm_btn.pack(side=tk.LEFT, padx=10)

        # 取消按钮
        cancel_btn = ttk.Button(
            btn_frame,
            text="取消",
            command=self.window.destroy,
            width=15
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def delete_selected(self):
        """删除选中的英雄"""
        # 获取要删除的英雄列表
        to_delete = [hero for hero, var in self.selected_heroes.items() if var.get()]

        if not to_delete:
            messagebox.showinfo("提示", "请至少选择一个英雄")
            return

        # 直接删除选中的英雄（不再弹出确认对话框）
        new_heroes = [hero for hero in self.heroes if hero not in to_delete]

        # 回调更新主窗口的英雄列表
        self.callback(new_heroes)

        # 关闭窗口
        self.window.destroy()


class AddHeroWindow:
    """增加英雄窗口类"""

    def __init__(self, parent, imgs_dict, callback):
        self.parent = parent
        self.imgs_dict = imgs_dict
        self.callback = callback

        # 创建二级窗口
        self.window = tk.Toplevel(parent)
        self.window.title("增加英雄")
        self.window.geometry("500x300")
        self.window.grab_set()  # 模态窗口

        # 标题
        title_label = ttk.Label(
            self.window,
            text="增加新英雄",
            font=('微软雅黑', 14, 'bold')
        )
        title_label.pack(pady=10)

        # 输入框框架
        input_frame = ttk.Frame(self.window)
        input_frame.pack(pady=20, padx=20, fill=tk.X)

        # 英雄名称标签
        hero_label = ttk.Label(input_frame, text="英雄名称:", font=('微软雅黑', 11))
        hero_label.pack(side=tk.LEFT, padx=5)

        # 英雄名称输入框（带下拉选项）
        self.hero_var = tk.StringVar()
        self.hero_combo = ttk.Combobox(
            input_frame,
            textvariable=self.hero_var,
            width=20,
            font=('微软雅黑', 11)
        )
        # 设置可选的英雄列表（来自图片字典的键）
        self.hero_combo['values'] = list(self.imgs_dict.keys())
        self.hero_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 预览图片标签
        self.preview_label = ttk.Label(self.window)
        self.preview_label.pack(pady=10)

        # 绑定选择事件
        self.hero_combo.bind('<<ComboboxSelected>>', self.show_preview)

        # 按钮框架
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=20)

        # 添加按钮
        add_btn = ttk.Button(
            btn_frame,
            text="添加",
            command=self.add_hero,
            width=15
        )
        add_btn.pack(side=tk.LEFT, padx=10)

        # 取消按钮
        cancel_btn = ttk.Button(
            btn_frame,
            text="取消",
            command=self.window.destroy,
            width=15
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def show_preview(self, event=None):
        """显示选中的英雄预览图"""
        hero_name = self.hero_var.get()
        if hero_name in self.imgs_dict:
            pil_img = self.imgs_dict[hero_name]
            # 调整图片大小
            pil_img = pil_img.resize((80, 80), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            self.preview_label.configure(image=tk_img)
            self.preview_label.image = tk_img  # 保持引用
        else:
            self.preview_label.configure(image='')

    def add_hero(self):
        """添加英雄到主列表"""
        hero_name = self.hero_var.get().strip()
        if not hero_name:
            messagebox.showwarning("输入错误", "请输入英雄名称")
            return

        # 直接调用回调函数添加英雄（不再弹出确认对话框）
        self.callback(hero_name)
        self.window.destroy()


if __name__ == '__main__':
    backend = BackEnd()
    gui = AutoPickerGUI(backend)
    gui.run()