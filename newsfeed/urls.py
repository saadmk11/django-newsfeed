from django.urls import path

from .views import IssueListView, IssueDetailView


app_name = 'newsfeed'

urlpatterns = [
    path('', IssueListView.as_view(), name='issue_list'),
    path('<slug:issue_number>/', IssueDetailView.as_view(), name='issue_detail'),
]
