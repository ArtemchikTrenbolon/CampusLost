from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('ads', views.AdViewSet, basename='ad')

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('buildings/', views.BuildingListView.as_view(), name='buildings'),
    path('', include(router.urls)),
]