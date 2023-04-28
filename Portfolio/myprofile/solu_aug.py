import cv2
import numpy as np
from PIL import Image
import random
import os
class Solu_aug():
    def __init__(self, input_path, output_path, class_n, back_path, txtfolder):# 1枚あたり20枚の画像を水増し
        # 入力画像の保存先パス
        self.input_path = input_path
        # 出力画像の保存先パス
        self.output_path = output_path
        self.wpn = 3 #射影変換の枚数(片方何枚か)
        self.size_n = 10 #一つの背景に張り付ける枚数
        if back_path == "":
            self.back_path = "C:\Solution\Generate_Image\images\\sweetsback"
        else:
            self.back_path = back_path
        
        if txtfolder == "":
            self.txtfolder = "C:\Solution\Generate_Image\images\item01\\txt"
        else:
            self.txtfolder = txtfolder
        self.class_n = class_n

    def gen_ori_image(self):
        # 入力画像を読み込み(-1指定でαチャンネルも読み取る)
        img = cv2.imread(self.input_path, -1)
        # αチャンネルが0となるインデックスを取得
        # ex) ([0, 1, 3, 3, ...],[2, 4, 55, 66, ...])
        # columnとrowがそれぞれ格納されたタプル(長さ２)となっている
        index = np.where(img[:, :, 3] == 0)
        # 白塗りする
        img[index] = [0, 0, 0, 255]
        # 出力
        cv2.imwrite(self.input_path, img)
    
    def generate_image(self):#一枚から傾けた画像を数枚生成する
        self.original_img = cv2.imread(self.input_path)
        self.item_name = self.input_path[39:-4]
        print(self.item_name)
        self.side = "_right_"

        #画像のサイズを整える
        height, width, channels = self.original_img.shape[:3]
        if height < width:#横長の時は
            self.original_img = cv2.resize(self.original_img, (300, int(height * 300 / width)))
        else:#縦長の時は
            self.original_img = cv2.resize(self.original_img, (int(width * 300 / height), 300))
        
        height, width, channels = self.original_img.shape[:3]
        #疑似的に射影を計算
        # 変換前後の対応点を設定
        for i in range(self.wpn):
            p_original = np.float32([[0,0], [width,0], [0, height], [width, height]])
            p_trans = np.float32([[0,0], 
                                  [width * (1 - i*10 / 100), (height - (height * 100 / (i*10 + 100))) / 2], 
                                  [0,height], 
                                  [width * (1 - i*10 / 100), (height + (height * 100 / (i*10 + 100))) / 2]]
                                  )
            # 変換マトリクスと射影変換
            M = cv2.getPerspectiveTransform(p_original, p_trans)
            gen_img = cv2.warpPerspective(self.original_img, M, (width, height))
            output_path = self.output_path + "\\" + self.item_name + "_right_" + str(i) + ".png"
            print(output_path)
            cv2.imwrite(output_path, gen_img)
        
        for i in range(self.wpn):
            p_original = np.float32([[0,0], [width,0], [0, height], [width, height]])
            p_trans = np.float32([[width*i*10/100, (height - (height * 100 / (i*10 + 100))) / 2], 
                                  [width, 0], 
                                  [width*i*10/100, (height + (height * 100 / (i*10 + 100))) / 2], 
                                  [width, height]])
            # 変換マトリクスと射影変換
            M = cv2.getPerspectiveTransform(p_original, p_trans)
            gen_img = cv2.warpPerspective(self.original_img, M, (width, height))
            output_path = self.output_path + "\\" + self.item_name + "_left_" + str(i) + ".png"
            print(output_path)
            cv2.imwrite(output_path, gen_img)

        
        for i in range(self.wpn * 2):#黒背景を透過する
            src = cv2.imread(self.output_path + "\\" + self.item_name + self.side + str(i%3) + ".png")
            # Point 1: 白色部分に対応するマスク画像を生成
            mask = np.all(src[:,:,:] == [0, 0, 0], axis=-1)
            # Point 2: 元画像をBGR形式からBGRA形式に変換
            dst = cv2.cvtColor(src, cv2.COLOR_BGR2BGRA)
            # Point3: マスク画像をもとに、白色部分を透明化
            dst[mask,3] = 0
            # png画像として出力
            cv2.imwrite(self.output_path + "\\" + self.item_name + self.side + str(i%3) + ".png", dst)
            if i == self.wpn/2 - 1:
                self.side = "_left_"
            
    #Resize ⇒透過
    def composite_photograph(self):
        #back_n = sum(os.path.isfile(os.path.join(dir, name)) for name in os.listdir(dir))
        folderfile = os.listdir(self.back_path)
        file = [f for f in folderfile if os.path.isfile(os.path.join(self.back_path, f))]
        print(file)
        print(len(file))
        for s in range(len(file)):#背景の分繰り返し
            print(file[s])
            self.back = Image.open("C:\Solution\Generate_Image\images\\sweetsback\\" + file[s])
            self.back = self.back.resize((960, 540))

            for i in range(self.wpn * 2):#射影変換で生成した分繰り返す
                if i == self.wpn / 2 - 1:
                    self.side = "_right_"
                back = self.back
                #img = cv2.imread(self.output_path + "\\" + self.item_name + self.side + str(i) + ".png")
                img = Image.open(self.output_path + "\\" + self.item_name + self.side + str(i % 3) + ".png")
                weight, height = img.size
                for m in range(self.size_n):#20回張り付ける
                    back =self.back.copy()
                    magnification = 0.5 + (m % 10)*0.1
                    new_img = img.resize((int(weight * magnification), int(height * magnification)))
                    x, y = new_img.size #resize後のサイズ
                    new_x = random.randint(0, 960 - x)#張り付ける座標
                    new_y = random.randint(0, 540 - y)
                    back.paste(new_img, (new_x,new_y), new_img)
                    output_path = self.output_path + "\\" + self.item_name + "_result_" + str(s)+"_" + str(i) +"_" +str(m) + ".png"
                    back.save(output_path)
                    f = open(self.txtfolder + "\\" + self.item_name + "_result_" + str(s)+"_" + str(i) +"_" +str(m) + ".txt", 'w')
                    x = (1 - (i%3) / 10) * x
                    f.write(str(self.class_n) + " " +
                            str(float((new_x + x / 2) / 960)) + " "+
                            str(float((new_y + y / 2)) / 540) + " "+
                            str(x/960) +" " + 
                            str(y/540))
                    f.close()

