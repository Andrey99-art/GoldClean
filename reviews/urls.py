from django.urls import path
from . import views

urlpatterns = [
    path('leave/', views.leave_review, name='leave_review'),
    path('success/', views.review_success, name='review_success'),
]