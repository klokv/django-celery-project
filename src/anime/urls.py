from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.anime_list_view),
    path('infinite/', views.anime_infinite_rating_view),
    path('<int:pk>/', views.anime_detail_view),
    path('popular/', views.anime_popular_view),
]
