import os
import threading
from time import sleep
import dxcam
from core.config import Config
from core.feature_matcher import FeatureMatcher
from core.utils import load_imgs
from PIL import Image


class BackEnd:
    def __init__(self):
        print("数据初始化中...")
        # 初始化匹配器
        self.matcher = FeatureMatcher(device='cuda')
        # 构建特征数据库（只需运行一次）
        self.img_dict = load_imgs(Config.pictrue_dir)  # imgs {name:ndarray}
        self.img_features = {}  # 向量数据库
        for k, v in self.img_dict.items():
            self.img_features[k] = self.matcher.extract_features(v)
        # 保存阵容数据
        self.lineups_dict = self.get_lineups()
        # 保存英雄图片
        self.imgs_dict = self.get_imgs()
        print("数据后端构建完成，请开始使用")

    def match(self,img):
        return self.matcher.match_images(img, self.img_features)

    def get_imgs(self):
        imgs_dict = {}
        for filename in os.listdir(Config.pictrue_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img_path = os.path.join(Config.pictrue_dir, filename)
                # 读取图片
                img = Image.open(img_path)
                if img is not None:
                    name = filename.split('.')[0]
                    imgs_dict[name] = img
                else:
                    print(f"警告：无法加载图片 {filename}")
        return imgs_dict



    def get_lineups(self):
        lineups_dict={}
        for i, filename in enumerate(os.listdir(Config.lineup_dir)):
            heros_path = os.path.join(Config.lineup_dir, filename)
            heros = self.get_heros(heros_path)
            lineups_dict[filename]=heros

        return lineups_dict

    def get_heros(self,heros_path):
        with open(heros_path, 'r', encoding='utf-8') as file:
            heros = [line.strip() for line in file]
        return heros




if __name__ == '__main__':
    pick=BackEnd()


