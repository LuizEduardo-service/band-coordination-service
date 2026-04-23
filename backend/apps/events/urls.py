from django.urls import path
from apps.invites.views import EventInviteCreateView
from .views import (
    EventListView, EventDetailView,
    EventMemberListView, EventMemberDetailView, ParticipationView,
    SongListView, SongDetailView,
    EventSongListView, EventSongDetailView,
    SongSuggestionCreateView,
    SongSuggestionPendingListView,
    SongSuggestionPendingCountView,
    SongSuggestionApproveView,
    SongSuggestionRejectView,
)

urlpatterns = [
    path('groups/<slug:slug>/events/', EventListView.as_view(), name='event_list'),
    path('groups/<slug:slug>/events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('groups/<slug:slug>/events/<int:pk>/invites/', EventInviteCreateView.as_view(), name='event_invite_create'),
    path('groups/<slug:slug>/events/<int:pk>/members/', EventMemberListView.as_view(), name='event_member_list'),
    path('groups/<slug:slug>/events/<int:pk>/members/<int:member_pk>/', EventMemberDetailView.as_view(), name='event_member_detail'),
    path('groups/<slug:slug>/events/<int:pk>/members/<int:member_pk>/participation/', ParticipationView.as_view(), name='participation'),
    path('groups/<slug:slug>/songs/', SongListView.as_view(), name='song_list'),
    path('groups/<slug:slug>/song-suggestions/', SongSuggestionCreateView.as_view(), name='song_suggestion_create'),
    path('groups/<slug:slug>/songs/<int:song_pk>/', SongDetailView.as_view(), name='song_detail'),
    path('song-suggestions/pending/', SongSuggestionPendingListView.as_view(), name='song_suggestion_pending_list'),
    path('song-suggestions/pending-count/', SongSuggestionPendingCountView.as_view(), name='song_suggestion_pending_count'),
    path('song-suggestions/<int:pk>/approve/', SongSuggestionApproveView.as_view(), name='song_suggestion_approve'),
    path('song-suggestions/<int:pk>/reject/', SongSuggestionRejectView.as_view(), name='song_suggestion_reject'),
    path('groups/<slug:slug>/events/<int:pk>/songs/', EventSongListView.as_view(), name='event_song_list'),
    path('groups/<slug:slug>/events/<int:pk>/songs/<int:esong_pk>/', EventSongDetailView.as_view(), name='event_song_detail'),
]
