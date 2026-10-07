from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/featured/shuffle/', views.featured_shuffle_api, name='featured_shuffle_api'),
    path('experiments/', views.experiment_list, name='experiment_list'),
    path('experiments/new/', views.experiment_create, name='experiment_create'),
    path('experiments/<uuid:uuid>/', views.experiment_detail, name='experiment_detail'),
    path('experiments/<uuid:uuid>/status/', views.experiment_status_api, name='experiment_status_api'),
    path('experiments/<uuid:uuid>/download/', views.experiment_download_zip, name='experiment_download_zip'),
    path('experiments/<uuid:uuid>/retry/', views.experiment_retry, name='experiment_retry'),
    path('experiments/claim/', views.experiment_claim, name='experiment_claim'),
    path('register/', views.register_view, name='register'),
    path('set-language/', views.set_language_custom, name='set_language_custom'),
]
