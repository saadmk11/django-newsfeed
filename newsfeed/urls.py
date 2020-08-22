from django.urls import path

from .views import (
    IssueDetailView,
    IssueListView,
    NewsletterSubscribeView,
    NewsletterSubscriptionConfirmView,
    NewsletterUnsubscribeView,
)


app_name = 'newsfeed'

urlpatterns = [
    path('issues/', IssueListView.as_view(), name='issue_list'),
    path(
        'issues/<slug:issue_number>/',
        IssueDetailView.as_view(),
        name='issue_detail'
    ),
    path(
        'subscribe/',
        NewsletterSubscribeView.as_view(),
        name='newsletter_subscribe'),
    path(
        'subscribe/confirm/<uuid:token>/',
        NewsletterSubscriptionConfirmView.as_view(),
        name='newsletter_subscribe_confirm'
    ),
    path(
        'unsubscribe/',
        NewsletterUnsubscribeView.as_view(),
        name='newsletter_unsubscribe'
    ),
]
