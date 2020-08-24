from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.detail import SingleObjectMixin

from .app_settings import (
    NEWSFEED_SUBSCRIPTION_REDIRECT_URL,
    NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL,
)
from .forms import SubscriberEmailForm
from .models import Issue, Post, Subscriber


class IssueListView(ListView):
    model = Issue
    paginate_by = 15
    template_name = 'newsfeed/issue_list.html'

    def get_queryset(self):
        return super().get_queryset().released()


class IssueDetailView(SingleObjectMixin, ListView):
    model = Post
    template_name = "newsfeed/issue_detail.html"
    slug_url_kwarg = 'issue_number'
    slug_field = 'issue_number'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(
            queryset=Issue.objects.released()
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issue'] = self.object
        return context

    def get_queryset(self):
        return self.object.posts.visible().select_related('category')


class SubscriptionAjaxResponseMixin(FormView):
    """Mixin to add Ajax support to the subscription form"""
    form_class = SubscriberEmailForm
    message = ''
    success = False

    def form_invalid(self, form):
        response = super().form_invalid(form)

        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            messages.error(self.request, self.message)
            return response

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.request.is_ajax():
            data = {
                'message': self.message,
                'success': self.success
            }
            return JsonResponse(data, status=200)
        else:
            messages.success(self.request, self.message)
            return response


class NewsletterSubscribeView(SubscriptionAjaxResponseMixin):
    template_name = "newsfeed/newsletter_subscribe.html"
    success_url = NEWSFEED_SUBSCRIPTION_REDIRECT_URL

    def form_valid(self, form):
        email_address = form.cleaned_data.get('email_address')

        subscriber, created = Subscriber.objects.get_or_create(
            email_address=email_address
        )

        if not created and subscriber.subscribed:
            self.success = False
            self.message = (
                'You have already subscribed to the newsletter.'
            )
        else:
            subscriber.send_verification_email(created)
            self.success = True
            self.message = (
                'Thank you for subscribing! '
                'Please check your email inbox to confirm '
                'your subscription to start receiving newsletters.'
            )

        return super().form_valid(form)


class NewsletterUnsubscribeView(SubscriptionAjaxResponseMixin):
    template_name = "newsfeed/newsletter_unsubscribe.html"
    success_url = NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL

    def form_valid(self, form):
        email_address = form.cleaned_data.get('email_address')

        subscriber = Subscriber.objects.filter(
            subscribed=True,
            email_address=email_address
        ).first()

        if subscriber:
            subscriber.unsubscribe()
            self.success = True
            self.message = (
                'You have successfully unsubscribed from the newsletter.'
            )
            messages.success(self.request, self.message)
        else:
            self.success = False
            self.message = (
                'Subscriber with this email address does not exist.'
            )
            messages.error(self.request, self.message)

        return super().form_valid(form)


class NewsletterSubscriptionConfirmView(DetailView):
    template_name = "newsfeed/newsletter_subscription_confirm.html"
    model = Subscriber
    slug_url_kwarg = 'token'
    slug_field = 'token'

    def get_queryset(self):
        return super().get_queryset().filter(verified=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        subscribed = self.object.subscribe()

        context = self.get_context_data(
            object=self.object, subscribed=subscribed
        )
        return self.render_to_response(context)
