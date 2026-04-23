from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from apps.common.mixins import GroupScopedMixin
from .models import Group, Membership
from .serializers import GroupSerializer, MembershipSerializer
from .permissions import IsGroupAdmin, IsGroupMember


class GroupListView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Group.objects.filter(memberships__user=self.request.user).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        Membership.objects.create(user=request.user, group=group, role='admin')
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = GroupSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Group.objects.filter(memberships__user=self.request.user).distinct()

    def get_object(self):
        obj = super().get_object()
        is_admin = IsGroupAdmin()
        is_admin.request = self.request
        is_admin.view = self
        is_admin.kwargs = {'slug': self.kwargs['slug']}

        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if not is_admin.has_permission(self.request, self):
                raise PermissionDenied()
        else:
            is_member = IsGroupMember()
            is_member.request = self.request
            is_member.view = self
            is_member.kwargs = {'slug': self.kwargs['slug']}
            if not is_member.has_permission(self.request, self):
                raise PermissionDenied()
        return obj

    def get_group(self):
        return Group.objects.get(slug=self.kwargs['slug'])


class MemberListView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        self.check_group_permission(IsGroupMember)
        group = self.get_group()
        memberships = Membership.objects.filter(group=group).select_related('user').order_by('user__username')
        return Response(
            MembershipSerializer(memberships, many=True, context={'request': request}).data
        )

    def post(self, request, slug):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        serializer = MembershipSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(group=group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MemberDetailView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return Membership.objects.get(pk=self.kwargs['pk'], group__slug=self.kwargs['slug'])
        except Membership.DoesNotExist:
            raise Http404('Membro não encontrado.')

    def patch(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        self.get_group()
        membership = self.get_object()
        serializer = MembershipSerializer(
            membership, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        self.get_group()
        membership = self.get_object()
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
