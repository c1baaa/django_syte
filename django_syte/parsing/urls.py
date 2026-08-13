from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


urlpatterns = [path('login/', views.login),
               path('register/', views.register),
               path('balance/<int:user_id>/', views.user_balance),
               path('cards/user/<int:user_id>/', views.user_cards),
               path('cards/add/', views.add_card),
               path('card_transfer/', views.card_transfer),
               path('transfers/', views.transfer_list),
               path('transfers/user/<int:user_id>/', views.user_transfer_list),
               path('payments/', views.make_payment),
               path('payments/<int:user_id>/', views.payment_list),
               path('profile/<int:user_id>/', views.profile),
               path('users/', views.user_list),]