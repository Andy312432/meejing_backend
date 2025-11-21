from rest_framework import serializers

from map.serializers import PlaceSerializer, PostSerializer


class SearchResultsSerializer(serializers.Serializer):
    places = PlaceSerializer(many=True)
    posts = PostSerializer(many=True)

class IdResultsSerializer(serializers.Serializer):
    places = PlaceSerializer(many=True)

