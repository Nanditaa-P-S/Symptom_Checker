from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_info, name='user_info'),
    path('symptoms/', views.symptom_form, name='symptom_form'),
    path('search/', views.search_tips, name='search_tips'),
    path('reminder/', views.medication_reminder, name='medication_reminder'),
    path('send-test-email/', views.send_test_email, name='send_test_email'),
    path('send-reminder/', views.send_medication_reminder, name='send_medication_reminder'),
    path('mongo-data/', views.mongo_data_view, name='mongo_data'),
]
