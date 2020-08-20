from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin

from .models import Issue, Post


class IssueListView(ListView):
    template_name = 'newsfeed/issue_list.html'
    model = Issue

    def get_queryset(self):
        return super().get_queryset().released()


class IssueDetailView(SingleObjectMixin, ListView):
    model = Post
    paginate_by = 20
    slug_url_kwarg = 'issue_number'
    slug_field = 'issue_number'
    template_name = "newsfeed/issue_detail.html"

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
        return self.object.posts.filter(
            is_visible=True
        ).select_related('category')
