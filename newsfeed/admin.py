"""Admin registration for newsfeed issues, posts, and subscribers."""

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from newsfeed.utils.send_newsletters import send_email_newsletter

from .models import Issue, Newsletter, Post, PostCategory, Subscriber


@admin.action(description="Publish issues now")
def publish_issues(
    _modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Issue],
) -> None:
    """Publish the selected issues."""
    updated = queryset.update(is_draft=False)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Successfully published {updated} issue(s)",
    )


@admin.action(description="Mark issues as draft")
def make_draft(
    _modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Issue],
) -> None:
    """Mark the selected issues as drafts."""
    updated = queryset.update(is_draft=True)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Successfully marked {updated} issue(s) as draft",
    )


@admin.action(description="Send newsletters")
def send_newsletters(
    _modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Newsletter],
) -> None:
    """Send the selected newsletters in this request.

    ``respect_schedule`` is false so a future schedule does not block a
    manual send. Replace this action with your own background task when
    delivery should leave the request. The README shows Django tasks and
    Celery.
    """
    send_email_newsletter(newsletters=queryset, respect_schedule=False)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Sending selected newsletters(s) to the subscribers",
    )


@admin.action(description="Hide posts from issue")
def hide_post(
    _modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Post],
) -> None:
    """Hide the selected posts."""
    updated = queryset.update(is_visible=False)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Successfully marked {updated} post(s) as hidden",
    )


@admin.action(description="Make posts visible")
def make_post_visible(
    _modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Post],
) -> None:
    """Make the selected posts visible."""
    updated = queryset.update(is_visible=True)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Successfully made {updated} post(s) visible",
    )


class PostInline(admin.TabularInline):
    """Inline editor for the posts that belong to an issue."""

    model = Post


class IssueAdmin(admin.ModelAdmin):
    """Admin for newsletter issues."""

    view_on_site = True
    date_hierarchy = "publish_date"
    list_display = (
        "issue_number",
        "title",
        "publish_date",
        "issue_type",
        "is_draft",
        "is_published",
    )
    list_filter = ("is_draft", "issue_type")
    search_fields = (
        "title",
        "short_description",
        "posts__title",
        "posts__short_description",
    )
    readonly_fields = ("created_at", "updated_at")
    sortable_by = ("issue_number", "publish_date")
    inlines = (PostInline,)
    actions = (publish_issues, make_draft)


class NewsletterAdmin(admin.ModelAdmin):
    """Admin for issue newsletters."""

    list_select_related = ("issue",)
    date_hierarchy = "schedule"
    list_display = (
        "subject",
        "issue",
        "is_sent",
        "schedule",
    )
    list_filter = ("is_sent",)
    search_fields = (
        "subject",
        "issue__short_description",
        "issue__title",
    )
    readonly_fields = ("created_at", "updated_at")
    sortable_by = ("schedule",)
    autocomplete_fields = ("issue",)
    actions = (send_newsletters,)


class PostAdmin(admin.ModelAdmin):
    """Admin for individual posts."""

    list_select_related = ("issue", "category")
    list_display = (
        "title",
        "category",
        "issue",
        "order",
        "is_visible",
    )
    list_filter = ("is_visible", "category")
    search_fields = (
        "title",
        "short_description",
        "issue__title",
        "issue__short_description",
        "category__title",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("issue", "category")
    actions = (hide_post, make_post_visible)


class PostCategoryAdmin(admin.ModelAdmin):
    """Admin for post categories."""

    list_display = ("name", "order")
    search_fields = ("name",)


class SubscriberAdmin(admin.ModelAdmin):
    """Admin for newsletter subscribers."""

    list_display = (
        "email_address",
        "subscribed",
        "verified",
        "token_expired",
        "verification_sent_date",
    )
    list_filter = (
        "subscribed",
        "verified",
        "verification_sent_date",
    )
    search_fields = ("email_address",)
    readonly_fields = ("created_at",)
    exclude = ("token",)


admin.site.register(Issue, IssueAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(PostCategory, PostCategoryAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
