from tensorflow.keras.utils import load_img, img_to_array
from keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

class Augmentation():
    def __init__(self, N_img, input_path, output_path):# 1枚あたり20枚の画像を水増し
        self.N_img = N_img
        # 入力画像の保存先パス
        self.input_path = input_path
        # 出力画像の保存先パス
        self.output_path = output_path
        
    def generate_image(self):
        if os.path.isdir(self.output_path) == False:
            os.mkdir(self.output_path)
        
        files = glob.glob(self.input_path + '/*.jpg')
        for i, file in enumerate(files):
        
            img = load_img(file)
            x = img_to_array(img)
            x = np.expand_dims(x, axis=0)
        
            # ImageDataGeneratorの生成
            datagen = ImageDataGenerator(
            zca_epsilon=1e-06,   # 白色化のイプシロン
            rotation_range=10.0, # ランダムに回転させる範囲
            width_shift_range=0.0, # ランダムに幅をシフトさせる範囲
            height_shift_range=0.0, # ランダムに高さをシフトさせる範囲
            brightness_range=None, # ランダムに明るさを変化させる範囲
            zoom_range=0.0,        # ランダムにズームさせる範囲
            horizontal_flip=True, # ランダムに水平方向に反転させる
            vertical_flip=True, # ランダムに垂直方向に反転させる
            )
        
            # 1枚あたり20枚の画像を水増し生成
            dg = datagen.flow(x, batch_size=1, save_to_dir=self.output_path, save_prefix='img', save_format='jpg')
            for i in range(self.N_img):
                batch = dg.next()
