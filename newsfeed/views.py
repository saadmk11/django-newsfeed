"""Public pages for issues and newsletter subscription."""

from django.contrib import messages
from django.db.models import Prefetch, QuerySet
from django.forms import Form
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from .app_settings import (
    NEWSFEED_SUBSCRIPTION_REDIRECT_URL,
    NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL,
)
from .forms import SubscriberEmailForm
from .models import Issue, Post, Subscriber
from .utils.check_ajax import is_ajax


class IssueListView(ListView):
    """Issue List View."""

    model = Issue
    paginate_by = 15
    template_name = "newsfeed/issue_list.html"

    def get_queryset(self) -> QuerySet[Issue]:
        """Return published issues.

        Returns:
            Issues that are public.

        """
        return super().get_queryset().released()


class IssueDetailView(SingleObjectMixin, ListView):
    """Issue Detail View."""

    model = Post
    template_name = "newsfeed/issue_detail.html"
    slug_url_kwarg = "issue_number"
    slug_field = "issue_number"

    def get(
        self,
        request: HttpRequest,
        *args: object,
        **kwargs: object,
    ) -> HttpResponse:
        """Show one published issue and its visible posts.

        Returns:
            The rendered issue page.

        """
        self.object = self.get_object(
            queryset=Issue.objects.released(),
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Add the issue to the post list context.

        Returns:
            Template context for the issue page.

        """
        context = super().get_context_data(**kwargs)
        context["issue"] = self.object
        return context

    def get_queryset(self) -> QuerySet[Post]:
        """Return the visible posts for this issue.

        Returns:
            Visible posts with their categories loaded.

        """
        return self.object.posts.visible().select_related("category")


class LatestIssueView(TemplateView):
    """Latest Issue View."""

    model = Post
    template_name = "newsfeed/latest_issue.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Add the newest issue to the template context.

        Returns:
            Template context including the newest issue.

        """
        prefetch_posts = Post.objects.visible().select_related("category")
        latest_issue = Issue.objects.prefetch_related(
            Prefetch("posts", queryset=prefetch_posts),
        ).first()

        context = super().get_context_data(**kwargs)
        context["latest_issue"] = latest_issue
        return context


class SubscriptionAjaxResponseMixin(FormView):
    """Mixin to add Ajax support to the subscription form."""

    form_class = SubscriberEmailForm
    message = ""
    success = False

    def form_invalid(self, form: Form) -> HttpResponse:
        """Return field errors for Ajax requests.

        Returns:
            A JSON error response for Ajax, otherwise the normal redirect.

        """
        response = super().form_invalid(form)

        if is_ajax(self.request):
            return JsonResponse(
                form.errors.get_json_data(),
                status=400,
            )
        messages.error(self.request, self.message)
        return response

    def form_valid(self, form: Form) -> HttpResponse:
        """Return the subscription result.

        Returns:
            A JSON result for Ajax, otherwise the normal redirect.

        """
        response = super().form_valid(form)

        if is_ajax(self.request):
            data = {
                "message": self.message,
                "success": self.success,
            }
            return JsonResponse(data, status=200)
        messages.success(self.request, self.message)
        return response


class NewsletterSubscribeView(SubscriptionAjaxResponseMixin):
    """Newsletter Subscribe View."""

    template_name = "newsfeed/newsletter_subscribe.html"
    success_url = NEWSFEED_SUBSCRIPTION_REDIRECT_URL

    def form_valid(self, form: Form) -> HttpResponse:
        """Create or reuse a subscriber and send confirmation mail.

        Returns:
            The shared subscription response.

        """
        email_address = form.cleaned_data.get("email_address")

        subscriber, created = Subscriber.objects.get_or_create(
            email_address=email_address,
        )

        if not created and subscriber.subscribed:
            self.success = False
            self.message = "You have already subscribed to the newsletter."
        else:
            subscriber.send_verification_email(created=created)
            self.success = True
            self.message = (
                "Thank you for subscribing! "
                "Please check your e-mail inbox to confirm "
                "your subscription and start receiving newsletters."
            )

        return super().form_valid(form)


class NewsletterUnsubscribeView(SubscriptionAjaxResponseMixin):
    """Newsletter Unsubscribe View."""

    template_name = "newsfeed/newsletter_unsubscribe.html"
    success_url = NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL

    def form_valid(self, form: Form) -> HttpResponse:
        """Unsubscribe a confirmed address.

        Returns:
            The shared subscription response.

        """
        email_address = form.cleaned_data.get("email_address")

        subscriber = Subscriber.objects.filter(
            subscribed=True,
            email_address=email_address,
        ).first()

        if subscriber:
            subscriber.unsubscribe()
            self.success = True
            self.message = (
                "You have successfully unsubscribed from the newsletter."
            )
        else:
            self.success = False
            self.message = "Subscriber with this e-mail address does not exist."

        return super().form_valid(form)


class NewsletterSubscriptionConfirmView(DetailView):
    """Newsletter Subscription Confirm View."""

    template_name = "newsfeed/newsletter_subscription_confirm.html"
    model = Subscriber
    slug_url_kwarg = "token"
    slug_field = "token"

    def get_queryset(self) -> QuerySet[Subscriber]:
        """Return subscribers who still need to confirm.

        Returns:
            Unverified subscribers.

        """
        return super().get_queryset().filter(verified=False)

    def get(
        self,
        _request: HttpRequest,
        *_args: object,
        **_kwargs: object,
    ) -> HttpResponse:
        """Confirm the subscriber identified by the token.

        Returns:
            The confirmation page.

        """
        self.object = self.get_object()
        subscribed = self.object.subscribe()

        context = self.get_context_data(
            object=self.object,
            subscribed=subscribed,
        )
        return self.render_to_response(context)
