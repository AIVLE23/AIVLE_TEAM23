from django.urls import path
from . import views

app_name='community'

urlpatterns = [
    path('', views.show_list, name='index'),
    path('detail/<int:pk>', views.detail, name="detail"),
    path('write/', views.write, name='write'),
    path('update/<int:id>', views.update, name='update'),
    path('delete/<int:id>/', views.delete, name='delete'),
]
