# from rest_framework.serializers import (
#     ModelSerializer,
#     Serializer,
#     CharField,
#     IntegerField,
# )
#
# from .models import TweetUser, Tweet, Hashtag
#
#
# class TweetUserSerializer(ModelSerializer):
#     class Meta:
#         model = TweetUser
#         fields = "__all__"
#
#
# class TweetSerializer(ModelSerializer):
#     class Meta:
#         model = Tweet
#         fields = "__all__"
#
#
# class HashTagSerializer(ModelSerializer):
#     class Meta:
#         model = Hashtag
#         fields = "__all__"
#
#
# class UserScoreSerializer(Serializer):
#     user_id = IntegerField()
#     screen_name = CharField()
#     description = CharField()
#     contact_tweet_text = CharField()
