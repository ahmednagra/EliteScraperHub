from django.urls import path
from . import views

urlpatterns = [
    path('', views.scrape_view, name='scrape_view'),
    path('download/', views.download_file, name='download'),
]


#
# from django.urls import path
# from . import views
#
# urlpatterns = [
#     path('', views.scrape_view, name='scrape_view'),
#     path('download/', views.download_file, name='download'),
#     path('run_script/', views.run_script, name='run_script'),
# ]
