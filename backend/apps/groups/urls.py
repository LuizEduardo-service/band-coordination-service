from django.urls import path
from .views import GroupListView, GroupDetailView, MemberListView, MemberDetailView
from apps.invites.views import GroupInviteCreateView

urlpatterns = [
    path('groups/', GroupListView.as_view(), name='group_list'),
    path('groups/<slug:slug>/', GroupDetailView.as_view(), name='group_detail'),
    path('groups/<slug:slug>/invites/', GroupInviteCreateView.as_view(), name='group_invite_create'),
    path('groups/<slug:slug>/members/', MemberListView.as_view(), name='member_list'),
    path('groups/<slug:slug>/members/<int:pk>/', MemberDetailView.as_view(), name='member_detail'),
]
