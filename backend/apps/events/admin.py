from django.contrib import admin
from .models import Event, EventMember, Song, EventSong, SongSuggestion

admin.site.register(Event)
admin.site.register(EventMember)
admin.site.register(Song)
admin.site.register(EventSong)
admin.site.register(SongSuggestion)
