from django.urls import path
from . import views


app_name = 'myprofile'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('GAN_page/', views.test.as_view(), name="GAN_page"),
    path('Image_Augmentation/', views.Image_AugmentationView.as_view(), name = "Image_Augmentation")
]