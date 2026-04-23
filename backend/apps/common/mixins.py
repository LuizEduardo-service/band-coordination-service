from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from apps.groups.models import Group


class GroupScopedMixin:
    def get_group(self):
        try:
            return Group.objects.get(slug=self.kwargs['slug'])
        except Group.DoesNotExist:
            raise Http404('Grupo não encontrado.')

    def check_group_permission(self, permission_class):
        permission = permission_class()
        if not permission.has_permission(self.request, self):
            raise PermissionDenied()
