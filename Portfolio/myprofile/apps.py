from django.apps import AppConfig
"""
import numpy as np
from torchvision import transforms
from torchvision import datasets
from torch.utils.data import DataLoader
from torch import nn
from skimage import io
import matplotlib.pyplot as plt
import glob
from torchvision import transforms
from tensorflow.keras.utils import load_img, img_to_array
import torch
"""
class MyprofileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myprofile'
"""   
class PixelNorm(nn.Module):
    def forward(self, x):
        eps = 1e-7
        mean = torch.mean(x**2, dim=1, keepdims=True)
        return x / (torch.sqrt(mean)+eps)

class WeightScale(nn.Module):
    def forward(self, x, gain=2):
        scale = (gain/x.shape[1])**0.5
        return x * scale

class MiniBatchStd(nn.Module):
    def forward(self, x):
        std = torch.std(x, dim=0, keepdim=True)
        mean = torch.mean(std, dim=(1,2,3), keepdim=True)
        n,c,h,w = x.shape
        mean = torch.ones(n,1,h,w, dtype=x.dtype, device=x.device)*mean
        return torch.cat((x,mean), dim=1)

class Conv2d(nn.Module):
    def __init__(self, inch, outch, kernel_size, padding=0):
        super().__init__()
        self.layers = nn.Sequential(
            WeightScale(),
            nn.ReflectionPad2d(padding),
            nn.Conv2d(inch, outch, kernel_size, padding=0),
            PixelNorm(),
            )
        nn.init.kaiming_normal_(self.layers[2].weight)

    def forward(self, x):
        return self.layers(x)

class ConvModuleG(nn.Module):
    '''
    Args:
        out_size: (int), Ex.: 16 (resolution)
        inch: (int),  Ex.: 256
        outch: (int), Ex.: 128
    '''
    def __init__(self, out_size, inch, outch, first=False):
        super().__init__()

        if first:
            layers = [
                Conv2d(inch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
                Conv2d(outch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
            ]

        else:
            layers = [
                nn.Upsample((out_size, out_size), mode='nearest'),
                Conv2d(inch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
                Conv2d(outch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
            ]

        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)

class ConvModuleD(nn.Module):
    '''
    Args:
        out_size: (int), Ex.: 16 (resolution)
        inch: (int),  Ex.: 256
        outch: (int), Ex.: 128
    '''
    def __init__(self, out_size, inch, outch, final=False):
        super().__init__()

        if final:
            layers = [
                MiniBatchStd(), # final block only
                Conv2d(inch+1, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
                Conv2d(outch, outch, 4, padding=0), 
                nn.LeakyReLU(0.2, inplace=False),
                nn.Conv2d(outch, 1, 1, padding=0), 
            ]
        else:
            layers = [
                Conv2d(inch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
                Conv2d(outch, outch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=False),
                nn.AdaptiveAvgPool2d((out_size, out_size)),
            ]

        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)

class Generator(nn.Module):
    def __init__(self):
        super().__init__()

        # conv modules & toRGBs
        scale = 1
        inchs  = np.array([512,256,128,64,32,16], dtype=np.uint32)*scale
        outchs = np.array([256,128, 64,32,16, 8], dtype=np.uint32)*scale
        sizes = np.array([4,8,16,32,64,128], dtype=np.uint32)
        firsts = np.array([True, False, False, False, False, False], dtype=np.bool)
        blocks, toRGBs = [], []
        for s, inch, outch, first in zip(sizes, inchs, outchs, firsts):
            blocks.append(ConvModuleG(s, inch, outch, first))
            toRGBs.append(nn.Conv2d(outch, 3, 1, padding=0))

        self.blocks = nn.ModuleList(blocks)
        self.toRGBs = nn.ModuleList(toRGBs)

    def forward(self, x, res, eps=1e-7):
        # to image
        n,c = x.shape
        x = x.reshape(n,c//16,4,4)

        # for the highest resolution
        res = min(res, len(self.blocks))

        # get integer by floor
        nlayer = max(int(res-eps), 0)
        for i in range(nlayer):
            x = self.blocks[i](x)

        # high resolution
        x_big = self.blocks[nlayer](x)
        dst_big = self.toRGBs[nlayer](x_big)

        if nlayer==0:
            x = dst_big
        else:
            # low resolution
            x_sml = torch.nn.functional.interpolate(x, x_big.shape[2:4], mode='nearest')
            dst_sml = self.toRGBs[nlayer-1](x_sml)
            alpha = res - int(res-eps)
            x = (1-alpha)*dst_sml + alpha*dst_big

        #return x, n, res
        return torch.sigmoid(x)

class Discriminator(nn.Module):
    def __init__(self):
        super().__init__()

        self.minbatch_std = MiniBatchStd()

        # conv modules & toRGBs
        scale = 1
        inchs = np.array([256,128, 64,32,16, 8], dtype=np.uint32)*scale
        outchs  = np.array([512, 256,128,64,32,16], dtype=np.uint32)*scale
        sizes = np.array([1, 4,8,16,32,64], dtype=np.uint32)
        finals = np.array([True, False, False, False, False, False], dtype=np.bool)
        blocks, fromRGBs = [], []
        for s, inch, outch, final in zip(sizes, inchs, outchs, finals):
            fromRGBs.append(nn.Conv2d(3, inch, 1, padding=0))
            blocks.append(ConvModuleD(s, inch, outch, final=final))

        self.fromRGBs = nn.ModuleList(fromRGBs)
        self.blocks = nn.ModuleList(blocks)

    def forward(self, x, res):
        # for the highest resolution
        res = min(res, len(self.blocks))

        # get integer by floor
        eps = 1e-7
        n = max(int(res-eps), 0)

        # high resolution
        x_big = self.fromRGBs[n](x)
        x_big = self.blocks[n](x_big)

        if n==0:
            x = x_big
        else:
            # low resolution
            x_sml = torch.nn.functional.adaptive_avg_pool2d(x, x_big.shape[2:4])
            x_sml = self.fromRGBs[n-1](x_sml)
            alpha = res - int(res-eps)
            x = (1-alpha)*x_sml + alpha*x_big

        for i in range(n):
            x = self.blocks[n-1-i](x)

        return x

def gradient_penalty(netD, real, fake, res, batch_size, gamma=1):
    device = real.device
    alpha = torch.rand(batch_size, 1, 1, 1, requires_grad=True).to(device)
    x = alpha*real + (1-alpha)*fake
    d_ = netD.forward(x, res)
    g = torch.autograd.grad(outputs=d_, inputs=x,
                            grad_outputs=torch.ones(d_.shape).to(device),
                            create_graph=True, retain_graph=True,only_inputs=True)[0]
    g = g.reshape(batch_size, -1)
    return ((g.norm(2,dim=1)/gamma-1.0)**2).mean()

"""
#データセットの設定
"""
class MyDataset(torch.utils.data.Dataset):
    def __init__(self, path):
        #フォルダ内の全ての画像をnumpy配列にして格納
        #image  array size
        img_size = (128,128)
        #load images Folder
        dir_name = path
        #File type
        file_type  = 'jpg'
        #load images and image to array
        img_list = glob.glob(dir_name + '/*.' + file_type)
        temp_img_array_list = []
        for img in img_list:
            temp_img = load_img(img,grayscale=False,target_size=(img_size))
            temp_img_array = img_to_array(temp_img) /255
            temp_img_array = temp_img_array.reshape([3,128,128])
            temp_img_array_list.append(temp_img_array)
        temp_img_array_list = np.array(temp_img_array_list)
        zero_len = len(temp_img_array_list)
        labels = []
        for i in range(zero_len):
            labels.append(0)
        labels = np.array(labels)
        self.features_values = temp_img_array_list
        self.labels = labels

    # len()を使用すると呼ばれる
    def __len__(self):
        return len(self.features_values)

    # 要素を参照すると呼ばれる関数    
    def __getitem__(self, idx):
        features_x = torch.FloatTensor(self.features_values[idx])
        labels = torch.LongTensor(self.labels[idx])
        return features_x, labels

class Gen_Image():
    def __init__(self, read_path, save_path, res_step, image_rate):
        self.read_path = read_path
        self.save_path = save_path
        self.res_step = res_step
        self.image_rate = image_rate

    def gen_image(self):
        mydatasets = MyDataset(self.read_path)
        bs = 5
        train_loader = torch.utils.data.DataLoader(dataset=mydatasets, 
                                            batch_size=bs,
                                            shuffle=True, 
                                            drop_last = True
                                            )
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

        netG = Generator().to(device)
        netD = Discriminator().to(device)
        netG_mavg = Generator().to(device) # moving average
        optG = torch.optim.Adam(netG.parameters(), lr=0.0005, betas=(0.0, 0.99))
        optD = torch.optim.Adam(netD.parameters(), lr=0.0005, betas=(0.0, 0.99))
        criterion = torch.nn.BCELoss()

        # training
        nepoch = 10
        losses = []
        res_step = self.res_step
        j = 0
        # constant random inputs
        z0 = torch.randn(16, 512*16).to(device)
        z0 = torch.clamp(z0, -1.,1.)
        for iepoch in range(nepoch):
            if j==res_step*6.5:
                optG.param_groups[0]['lr'] = 0.0001
                optD.param_groups[0]['lr'] = 0.0001

            for i, data in enumerate(train_loader):
                x, y = data
                x = x.to(device)
                res = j/res_step

                ### train generator ###
                z = torch.randn(bs, 512*16).to(x.device)
                x_ = netG.forward(z, res)
                d_ = netD.forward(x_, res) # fake
                lossG = -d_.mean() # WGAN_GP

                optG.zero_grad()
                lossG.backward()
                optG.step()

                # update netG_mavg by moving average
                momentum = 0.995 # remain momentum
                alpha = min(1.0-(1/(j+1)), momentum)
                for p_mavg, p in zip(netG_mavg.parameters(), netG.parameters()):
                    p_mavg.data = alpha*p_mavg.data + (1.0-alpha)*p.data

                ### train discriminator ###
                z = torch.randn(x.shape[0], 512*16).to(x.device)
                x_ = netG.forward(z, res)
                x = torch.nn.functional.adaptive_avg_pool2d(x, x_.shape[2:4])
                d = netD.forward(x, res)   # real
                d_ = netD.forward(x_, res) # fake
                loss_real = -d.mean()
                loss_fake = d_.mean()
                loss_gp = gradient_penalty(netD, x.data, x_.data, res, x.shape[0])
                loss_drift = (d**2).mean()

                beta_gp = 10.0
                beta_drift = 0.001
                lossD = loss_real + loss_fake + beta_gp*loss_gp + beta_drift*loss_drift

                optD.zero_grad()
                lossD.backward()
                optD.step()

                print('ep: %02d %04d %04d lossG=%.10f lossD=%.10f' %
                        (iepoch, i, j, lossG.item(), lossD.item()))

                losses.append([lossG.item(), lossD.item()])
                j += 1

                if j%self.image_rate==0:
                    netG_mavg.eval()
                    z = torch.randn(16, 512*16).to(x.device)
                    x_0 = netG_mavg.forward(z0, res)
                    x_ = netG_mavg.forward(z, res)

                    dst = torch.cat((x_0, x_), dim=0)
                    dst = torch.nn.functional.interpolate(dst, (128, 128), mode='nearest')
                    dst = dst.to('cpu').detach().numpy()
                    n, c, h, w = dst.shape
                    dst = dst.reshape(4,8,c,h,w)
                    dst = dst.transpose(0,3,1,4,2)
                    dst = dst.reshape(4*h,8*w,3)
                    dst = np.clip(dst*255., 0, 255).astype(np.uint8)
                    io.imsave(self.save_path + '/img_%03d_%05d.png' % (iepoch, j), dst)
                    losses_ = np.array(losses)
                    niter = losses_.shape[0]//100*100
                    x_iter = np.arange(100)*(niter//100) + niter//200
                    plt.plot(x_iter, losses_[:niter,0].reshape(100,-1).mean(1))
                    plt.plot(x_iter, losses_[:niter,1].reshape(100,-1).mean(1))
                    plt.tight_layout()
                    plt.savefig(self.save_path + '/loss_%03d_%05d.png' % (iepoch, j))
                    plt.clf()

                    netG_mavg.train()

                if j >= res_step*7:
                    break

            if j >= res_step*7:
                break
"""