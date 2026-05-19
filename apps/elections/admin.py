from django.contrib import admin
from .models import Election, CandidateResult, VoteGoal


class CandidateResultInline(admin.TabularInline):
    model = CandidateResult
    extra = 0


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('year', 'election_type', 'round_number')
    list_filter = ('year', 'election_type')
    inlines = [CandidateResultInline]


@admin.register(CandidateResult)
class CandidateResultAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'party', 'city', 'election', 'votes', 'percentage', 'is_sorgatto')
    list_filter = ('election', 'party', 'is_sorgatto', 'city__region')
    search_fields = ('candidate_name', 'city__name')


@admin.register(VoteGoal)
class VoteGoalAdmin(admin.ModelAdmin):
    list_display = ('level', 'region', 'city', 'target_votes', 'current_estimate', 'progress_percentage', 'election_year')
    list_filter = ('level', 'election_year')
