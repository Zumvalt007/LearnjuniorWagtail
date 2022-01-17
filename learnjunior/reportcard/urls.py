from django.urls import path
from .views import ReportCardView

urlpatterns = [
    path('', ReportCardView.as_view()),
]