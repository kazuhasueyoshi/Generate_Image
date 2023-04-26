from django.shortcuts import render
from django.views import generic
from . import apps
from . import augmentation
from . import solu_aug
import cv2

# Create your views here.
class IndexView(generic.TemplateView):
    template_name = "index.html"
    #おそらく初期設定
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "ほーむがめん"
        return context
    #get処理
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    #post処理
    def post(self, request, *args, **kwargs):
        context = {
            'message': request.POST['message'],
        }
        return render(request, self.template_name, context)


class test(generic.TemplateView):
    template_name = "GAN_page.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        self.context = {
            "message" : "適切に入力してください。",
            "read_path" : "test",
            "save_path" : "test",
            "res_step" : "test",
            "image_rate" : "image_rate"
        }
        return self.context
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            read_path = request.POST['read_path']
            save_path = request.POST['save_path']
            res_step = request.POST['res_step']
            image_rate = request.POST['image_rate']
        
        self.context = {
            "read_path": read_path,
            "save_path": save_path,
            "res_step": res_step,
            "image_rate": image_rate,
        }
        try:
            res_step = int(res_step)
            image_rate = int(image_rate)
            gi = apps.Gen_Image(read_path, save_path, res_step, image_rate)
            gi.gen_image()
            self.context["message"] = "成功です。フォルダを確認してください。"
        except:
            self.context["message"] = "エラーが起きました。"
            pass
        return render(request, "GAN_page.html", self.context)
        #post以外にルーティングできない問題を早急に解決すべし。


class Image_AugmentationView(generic.TemplateView):
    def __init__(self):
        self.template_name = "Image_Augmentation.html"

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        self.context = {
            "message" : "message",
            "input_path" : "test",
            "output_step" : "test",
        }
        return self.context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if "generate" in request.POST:
                input_path = request.POST['input_path']
                output_path = request.POST['output_path']
                class_n = request.POST['class_n']
                back_path = request.POST['back_path']
                txtfolder = request.POST['txtfolder']
        
                self.context = {
                    "input_path": input_path,
                    "output_path": output_path,
                    "class_n" : class_n,
                    "back_path" : back_path,
                    "txtfolder" : txtfolder
                }
                
                #try:
                sa = solu_aug.Solu_aug(input_path, output_path, class_n, back_path, txtfolder)
                sa.generate_image()
                sa.composite_photograph()
                self.context["message"] = "成功です。フォルダを確認してください。"
                #except:
                #    self.context["message"] = "エラーが起きました。"
                #    pass
                return render(request, self.template_name, self.context)
                #post以外にルーティングできない問題を早急に解決すべし。
