from django.urls import path
from .views import (
    InviteListView,
    InvitePendingCountView,
    InviteAcceptView,
    InviteDeclineView,
)

urlpatterns = [
    path('invites/', InviteListView.as_view(), name='invite_list'),
    path('invites/pending-count/', InvitePendingCountView.as_view(), name='invite_pending_count'),
    path('invites/<int:pk>/accept/', InviteAcceptView.as_view(), name='invite_accept'),
    path('invites/<int:pk>/decline/', InviteDeclineView.as_view(), name='invite_decline'),
]
