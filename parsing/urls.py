from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
from parsing.views import CurrencyViewSet


router = DefaultRouter()
router.register(r'currency', CurrencyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("register/", views.register),
    path("login/", views.login),
    path("users/", views.user_list),
    path("transfer/", views.make_transfer),
    path("transfers/", views.transfer_list),
    path("balance/<int:user_id>/", views.user_balance),
    path("card_transfer/", views.card_transfer),
    path("add_card/", views.add_card),
    path("cards/<int:user_id>/", views.user_cards),
    path("card_transfer/", views.card_transfer),
    path("pay/", views.make_payment),
    path("payments/<int:user_id>/", views.payment_list),
    path("profile/<int:user_id>/", views.profile),

    ]