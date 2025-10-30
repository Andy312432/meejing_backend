from rest_framework import serializers

from journals.serializers import (
    JournalEntrySummarySerializer,
    JournalTagSerializer,
    LocationSerializer,
)


class SearchResultsSerializer(serializers.Serializer):
    entries = JournalEntrySummarySerializer(many=True)
    locations = LocationSerializer(many=True)
    tags = JournalTagSerializer(many=True)

