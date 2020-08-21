from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin

from .models import Issue, Post


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
