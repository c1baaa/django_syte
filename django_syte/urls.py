# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from parsing.views import CurrencyViewSet



urlpatterns = [
    path('', include('parsing.urls'))
]
