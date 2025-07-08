from django.urls import path
from . import views

urlpatterns = [
    path('', views.predict, name='predict'),
    path('send-report/', views.send_report, name='send_report'),
    path('clear-session/', views.clear_session, name='clear_session'),
]