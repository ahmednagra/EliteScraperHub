# from django.urls import path
#
# from .views import HomePageView
#
# urlpatterns = [
#     path('', HomePageView.as_view()),
# ]


from django.urls import path
from .views import HomePageView, download_file

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('download/<str:filename>', download_file, name='download_file'),
]
