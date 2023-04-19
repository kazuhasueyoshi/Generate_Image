import cv2
import numpy as np
class Solu_aug():
    def __init__(self, input_path, output_path):# 1枚あたり20枚の画像を水増し
        # 入力画像の保存先パス
        self.input_path = input_path
        # 出力画像の保存先パス
        self.output_path = output_path
        
    def generate_image(self):
        self.original_img = cv2.imread(self.input_path)
        #画像のサイズを整える
        height, width, channels = self.original_img.shape[:3]
        if height < width:#横長の時は
            self.original_img = cv2.resize(self.original_img, (600, int(height * 600 / width)))
        else:#縦長の時は
            self.original_img = cv2.resize(self.original_img, (int(width * 600 / height), 600))
        
        height, width, channels = self.original_img.shape[:3]
        #疑似的に射影を計算
        # 変換前後の対応点を設定
        for i in range(20):
            p_original = np.float32([[0,0], [width,0], [0, height], [width, height]])
            p_trans = np.float32([[0,0], [width * (1 - i / 100), (height - (height * 100 / (i + 100))) / 2], [0,height], [width * (1 - i / 100), (height + (height * 100 / (i + 100))) / 2]])
            # 変換マトリクスと射影変換
            M = cv2.getPerspectiveTransform(p_original, p_trans)
            gen_img = cv2.warpPerspective(self.original_img, M, (width, height))
            output_path = self.output_path + "/" + str(i) + "_gen_right.png"
            print(output_path)
            cv2.imwrite(output_path, gen_img)
        
        for i in range(20):
            p_original = np.float32([[0,0], [width,0], [0, height], [width, height]])
            p_trans = np.float32([[width*i/100, (height - (height * 100 / (i + 100))) / 2], 
                                  [width, 0], 
                                  [width*i/100, (height + (height * 100 / (i + 100))) / 2], 
                                  [width, height]])
            # 変換マトリクスと射影変換
            M = cv2.getPerspectiveTransform(p_original, p_trans)
            gen_img = cv2.warpPerspective(self.original_img, M, (width, height))
            output_path = self.output_path + "/" + str(i) + "_gen_left.png"
            print(output_path)
            cv2.imwrite(output_path, gen_img)