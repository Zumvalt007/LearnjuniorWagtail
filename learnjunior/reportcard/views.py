from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import query
from django.shortcuts import render
from learnjunior.home.models import QuizformSubmission
from django.views.generic import ListView
from django.contrib.auth import get_user_model
# Create your views here.
from wagtail.documents import get_document_model
import json
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
import os
import pandas as pd

User = get_user_model()
Documents = get_document_model()


class ReportCardView(LoginRequiredMixin, ListView):
    model = QuizformSubmission
    login_url = settings.LOGIN_URL
    redirect_field_name = 'next'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user_id = self.request.user.id)
        print(queryset)

        return queryset