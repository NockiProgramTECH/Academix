from django.urls import path
from .views import ParentSignUpView, ParentDashboardView

urlpatterns = [
    # Inscription pour un nouveau Parent
    path('signup/', ParentSignUpView.as_view(), name='parent_signup'),
    
    # Vue Dashboard connectée
    path('dashboard/', ParentDashboardView.as_view(), name='parent_dashboard'),
]
