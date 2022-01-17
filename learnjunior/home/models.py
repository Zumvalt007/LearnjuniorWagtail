from re import template
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.conf import settings
from django.db.models.base import Model
from django.db.models.deletion import CASCADE
from django.views.generic.detail import DetailView
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.search import index
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtailstreamforms.blocks import WagtailFormBlock
from django.utils.translation import ugettext_lazy as _
from wagtail.core import hooks
from django.contrib import messages
from django.shortcuts import redirect
from wagtailstreamforms.utils.requests import get_form_instance_from_request
from django.template.response import TemplateResponse

from wagtailstreamforms.models import FormSubmissionFile
from wagtailstreamforms.serializers import FormSubmissionSerializer

import json
from django.template.defaultfilters import pluralize


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        StreamFieldPanel('body', classname="full"),
    ]


class QuizPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('form', WagtailFormBlock()),
    ])

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        StreamFieldPanel('body', classname="full"),
    ]


class QuizformSubmission(models.Model):
    form_id = models.CharField(max_length=10)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    form_data = models.JSONField()
    submission_tms = models.DateTimeField(auto_now=True)


@hooks.register('before_serve_page')
def process_form(page, request, *args, **kwargs):
    """ Process the form if there is one, if not just continue. """

    if request.method == 'POST':
        form_def = get_form_instance_from_request(request)
        if form_def:
            form = form_def.get_form(request.POST, request.FILES, page=page, user=request.user)
            context = page.get_context(request, *args, **kwargs)
            if form.is_valid():
                # process the form submission
                submission_data = form.cleaned_data.copy()
                for field in form.files.keys():
                    count = len(form.files.getlist(field))
                    submission_data[field] = "{} file{}".format(count, pluralize(count))

                QuizformSubmission.objects.create(
                    form_id = request.POST.get('form_id'),
                    user = request.user,
                    form_data=json.dumps(submission_data, cls=FormSubmissionSerializer),
                    )
                
                # form_def.process_form_submission(form)
                # create success message
                if form_def.success_message:
                    messages.success(request, form_def.success_message, fail_silently=True)

                # redirect to the page defined in the form
                # or the current page as a fallback - this will avoid refreshing and submitting again
                redirect_page = form_def.post_redirect_page or page

                return redirect(redirect_page.get_url(request), context=context)

            else:
                # update the context with the invalid form and serve the page
                # IMPORTANT you must set these so that the when the form in the streamfield is
                # rendered it knows that it is the form that is invalid
                context.update({
                    'invalid_stream_form_reference': form.data.get('form_reference'),
                    'invalid_stream_form': form
                })

                # create error message
                if form_def.error_message:
                    messages.error(request, form_def.error_message, fail_silently=True)

                return TemplateResponse(
                    request,
                    page.get_template(request, *args, **kwargs),
                    context
                )

