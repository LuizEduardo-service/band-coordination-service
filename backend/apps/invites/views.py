from django.db import transaction
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import CustomUser
from apps.accounts.utils import get_user_instruments
from apps.common.mixins import GroupScopedMixin
from apps.events.models import Event, EventMember
from apps.groups.models import Group, Membership
from apps.groups.permissions import IsGroupAdmin

from .models import Invite
from .serializers import (
    InviteSerializer,
    GroupInviteCreateSerializer,
    EventInviteCreateSerializer,
)


class InviteListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Invite.objects.filter(invitee=request.user).select_related(
            'inviter', 'group', 'event', 'event__group'
        )
        st = request.query_params.get('status')
        if st in dict(Invite.STATUS_CHOICES):
            qs = qs.filter(status=st)
        qs = qs.order_by('-created_at')
        return Response(InviteSerializer(qs, many=True, context={'request': request}).data)


class InvitePendingCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        n = Invite.objects.filter(invitee=request.user, status=Invite.STATUS_PENDING).count()
        return Response({'count': n})


class InviteAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            try:
                inv = Invite.objects.select_for_update().get(
                    pk=pk,
                    invitee=request.user,
                    status=Invite.STATUS_PENDING,
                )
            except Invite.DoesNotExist:
                raise Http404('Convite não encontrado.')

            if inv.kind == Invite.KIND_GROUP:
                if Membership.objects.filter(user=inv.invitee, group=inv.group).exists():
                    raise ValidationError({'detail': 'Você já é membro deste grupo.'})
                Membership.objects.create(
                    user=inv.invitee,
                    group=inv.group,
                    role=inv.role if inv.role in ('admin', 'member') else 'member',
                )
            else:
                event = inv.event
                if Membership.objects.filter(user=inv.invitee, group=event.group).exists():
                    raise ValidationError(
                        {'detail': 'Você já participa do grupo; peça para ser adicionado ao evento pela escala.'}
                    )
                if EventMember.objects.filter(event=event, guest_user=inv.invitee).exists():
                    raise ValidationError({'detail': 'Você já está neste evento.'})
                inst = list(inv.instruments or [])
                if len(inst) < 1:
                    raise ValidationError({'instruments': 'Convite sem instrumentos.'})
                allowed = set(get_user_instruments(inv.invitee))
                if not allowed:
                    raise ValidationError({'detail': 'Cadastre instrumentos no perfil antes de aceitar.'})
                for i in inst:
                    if i not in allowed:
                        raise ValidationError({'instruments': f'Instrumento "{i}" não está no seu perfil.'})
                EventMember.objects.create(
                    event=event,
                    membership=None,
                    guest_user=inv.invitee,
                    participation='pending',
                    role_in_event=inv.role_in_event or '',
                    instruments=inst,
                )

            inv.mark_responded(Invite.STATUS_ACCEPTED)

        inv.refresh_from_db()
        return Response(InviteSerializer(inv, context={'request': request}).data)


class InviteDeclineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            inv = Invite.objects.get(
                pk=pk,
                invitee=request.user,
                status=Invite.STATUS_PENDING,
            )
        except Invite.DoesNotExist:
            raise Http404('Convite não encontrado.')
        inv.mark_responded(Invite.STATUS_DECLINED)
        return Response(InviteSerializer(inv, context={'request': request}).data)


class GroupInviteCreateView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        ser = GroupInviteCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        invitee_id = ser.validated_data['invitee_id']
        role = ser.validated_data['role']
        try:
            invitee = CustomUser.objects.get(pk=invitee_id)
        except CustomUser.DoesNotExist:
            raise ValidationError({'invitee_id': 'Usuário não encontrado.'})
        if invitee_id == request.user.id:
            raise ValidationError({'invitee_id': 'Não é possível convidar a si mesmo.'})
        if Membership.objects.filter(user_id=invitee_id, group=group).exists():
            raise ValidationError({'detail': 'Usuário já é membro do grupo.'})
        if Invite.objects.filter(
            invitee_id=invitee_id,
            group=group,
            kind=Invite.KIND_GROUP,
            status=Invite.STATUS_PENDING,
        ).exists():
            raise ValidationError({'detail': 'Já existe convite pendente para este usuário.'})

        inv = Invite.objects.create(
            inviter=request.user,
            invitee=invitee,
            kind=Invite.KIND_GROUP,
            group=group,
            role=role,
        )
        return Response(InviteSerializer(inv, context={'request': request}).data, status=status.HTTP_201_CREATED)


class EventInviteCreateView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        try:
            event = Event.objects.select_related('group').get(pk=pk, group__slug=slug)
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')

        ser = EventInviteCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        invitee_id = ser.validated_data['invitee_id']
        instruments = ser.validated_data['instruments']
        role_in_event = ser.validated_data.get('role_in_event') or ''

        try:
            invitee = CustomUser.objects.get(pk=invitee_id)
        except CustomUser.DoesNotExist:
            raise ValidationError({'invitee_id': 'Usuário não encontrado.'})
        if invitee_id == request.user.id:
            raise ValidationError({'invitee_id': 'Não é possível convidar a si mesmo.'})
        if Membership.objects.filter(user_id=invitee_id, group=event.group).exists():
            raise ValidationError(
                {'detail': 'Usuário já é do grupo; adicione-o ao evento pela lista de membros.'}
            )
        if EventMember.objects.filter(event=event, guest_user_id=invitee_id).exists():
            raise ValidationError({'detail': 'Usuário já está escalado neste evento.'})
        if EventMember.objects.filter(event=event, membership__user_id=invitee_id).exists():
            raise ValidationError({'detail': 'Usuário já está escalado neste evento.'})

        allowed = set(get_user_instruments(invitee))
        if not allowed:
            raise ValidationError({'detail': 'O convidado precisa ter instrumentos no perfil.'})
        for i in instruments:
            if i not in allowed:
                raise ValidationError({'instruments': f'Instrumento "{i}" não está no perfil do convidado.'})

        if Invite.objects.filter(
            invitee_id=invitee_id,
            event=event,
            kind=Invite.KIND_EVENT,
            status=Invite.STATUS_PENDING,
        ).exists():
            raise ValidationError({'detail': 'Já existe convite pendente para este usuário neste evento.'})

        inv = Invite.objects.create(
            inviter=request.user,
            invitee=invitee,
            kind=Invite.KIND_EVENT,
            group=event.group,
            event=event,
            instruments=instruments,
            role_in_event=role_in_event,
        )
        return Response(InviteSerializer(inv, context={'request': request}).data, status=status.HTTP_201_CREATED)
