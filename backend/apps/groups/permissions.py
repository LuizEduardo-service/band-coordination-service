from rest_framework.permissions import BasePermission
from .models import Membership


def user_can_access_event(user, slug: str, event_pk: int) -> bool:
    from apps.events.models import Event, EventMember

    try:
        event = Event.objects.select_related('group').get(pk=event_pk, group__slug=slug)
    except Event.DoesNotExist:
        return False
    if Membership.objects.filter(user=user, group=event.group).exists():
        return True
    return EventMember.objects.filter(event=event, guest_user=user).exists()


class IsGroupMemberOrEventGuest(BasePermission):
    """Membro do grupo ou convidado (somente evento) escalado no evento."""

    def has_permission(self, request, view):
        slug = view.kwargs.get('slug')
        pk = view.kwargs.get('pk')
        if not slug or pk is None:
            return False
        return user_can_access_event(request.user, slug, int(pk))


class IsGroupMember(BasePermission):
    def has_permission(self, request, view):
        group = view.get_group()
        return Membership.objects.filter(user=request.user, group=group).exists()


class IsGroupAdmin(BasePermission):
    def has_permission(self, request, view):
        group = view.get_group()
        return Membership.objects.filter(user=request.user, group=group, role='admin').exists()
