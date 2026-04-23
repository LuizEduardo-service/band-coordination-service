from django.contrib import admin
from .models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'status', 'inviter', 'invitee', 'group', 'event', 'created_at')
    list_filter = ('kind', 'status')
    raw_id_fields = ('inviter', 'invitee', 'group', 'event')
