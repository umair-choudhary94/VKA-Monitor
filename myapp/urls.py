
from django.urls import path
from .views import *
urlpatterns = [
    
    path('',crcl),
    path("calculate_dosage/",calculate_dosage,name="calculate_dosage")
]