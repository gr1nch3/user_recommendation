from math import log
from collections import defaultdict
from urllib.parse import unquote
from django.db.models import Q, Count
from rest_framework.decorators import api_view
from rest_framework.views import Response, status

from .models import TweetUser, Tweet, Hashtag

valid_languages = ["ar", "en", "fr", "in", "pt", "es", "tr", "ja"]


# Create your views here.
class RankingScore:
    def __init__(self, user_id, query_type, phrase, hashtag):
        self.user_id = user_id
        self.query_type = query_type
        self.phrase = phrase
        self.hashtag = hashtag

    def calculate_interaction_scores(self):
        """
        The interaction is defined as either a reply or retweet
        between user a and other users. Using that, we are going to fetch data
        and based on the availability, we'll get our result
        """
        user_a_replied = (
            Tweet.objects.filter(
                user_id=self.user_id,
                reply_to_user__isnull=False,
                lang__in=valid_languages,
            )
            .exclude(reply_to_user_id=self.user_id)
            .values("reply_to_user_id")
            .annotate(reply_count=Count("id"))
        )
        user_b_replied = (
            Tweet.objects.filter(
                reply_to_user_id=self.user_id,
                lang__in=valid_languages,
            )
            .exclude(user_id=self.user_id)
            .values("user_id")
            .annotate(reply_count=Count("id"))
        )
        user_a_retweeted = (
            Tweet.objects.filter(
                user_id=self.user_id,
                retweet__isnull=False,
                lang__in=valid_languages,
            )
            .values("retweet__user_id")
            .annotate(retweet_count=Count("id"))
        )

        user_b_retweeted = (
            Tweet.objects.filter(
                retweet__user_id=self.user_id,
                lang__in=valid_languages,
            )
            .values("user_id")
            .annotate(retweet_count=Count("id"))
        )

        # using these two to ensure proper calculation at the end
        reply_interaction_scores = defaultdict(int)
        retweet_interaction_scores = defaultdict(int)

        for reply in user_a_replied:
            target_user_id = reply["reply_to_user_id"]
            reply_count = reply["reply_count"]
            reply_interaction_scores[target_user_id] += reply_count

        for reply in user_b_replied:
            source_user_id = reply["user_id"]
            reply_count = reply["reply_count"]
            if source_user_id in reply_interaction_scores:
                reply_interaction_scores[source_user_id] += reply_count
            else:
                reply_interaction_scores[source_user_id] = reply_count

        for retweet in user_a_retweeted:
            target_user_id = retweet["retweet__user_id"]
            retweet_count = retweet["retweet_count"]
            if target_user_id in retweet_interaction_scores:
                retweet_interaction_scores[target_user_id] += retweet_count
            else:
                retweet_interaction_scores[target_user_id] = retweet_count

        for retweet in user_b_retweeted:
            source_user_id = retweet["user_id"]
            retweet_count = retweet["retweet_count"]
            if source_user_id in retweet_interaction_scores:
                retweet_interaction_scores[source_user_id] += retweet_count
            else:
                retweet_interaction_scores[source_user_id] = retweet_count

        interaction_scores = {}
        # since we have replies and retweets, we want to make sure all ids
        # have the proper count values
        all_users = set(reply_interaction_scores.keys()).union(
            set(retweet_interaction_scores.keys())
        )

        for user in all_users:
            reply_count = reply_interaction_scores.get(user, 0)
            retweet_count = retweet_interaction_scores.get(user, 0)
            interaction_scores[user] = log(1 + 2 * reply_count + retweet_count)

        return interaction_scores

    def get_valid_user_hashtags(self, tag):
        """
        Checking for other users that may have use the same hashtag as the user
        """
        # prioritizing the tag before the user in search
        hashtags = (
            Hashtag.objects.filter(text__icontains=tag, is_popular=False)
            .values("tweet__user_id")
            .annotate(count=Count("text"))
        )
        # prioritizing the user in result and then the count of the tag
        return {hashtag["tweet__user_id"]: hashtag["count"] for hashtag in hashtags}

    def calculate_hashtag_scores(self):
        """
        Calculating th ehashtag scores user the user id given and hashtags used by the
        given user to find others
        """
        hashtags = (
            Hashtag.objects.filter(tweet__user_id=self.user_id, is_popular=False)
            .values("text")
            .annotate(count=Count("text"))
        )

        # using defaultdict to avoid key error
        hashtag_scores = defaultdict(float)
        for hashtag in hashtags:
            text = hashtag["text"].lower()
            count = hashtag["count"]

            valid_user_hashtags = self.get_valid_user_hashtags(text)
            for other_user_id, other_count in valid_user_hashtags.items():
                same_tag_count = (
                    count + other_count if other_user_id != self.user_id else 1
                )
                if same_tag_count > 10:
                    hashtag_scores[other_user_id] += 1 + log(1 + same_tag_count - 10)
                else:
                    hashtag_scores[other_user_id] += 1

        return hashtag_scores

    def calculate_keywords_score(self):
        """
        Keyword scores between users that have contacted each other. The contact is defined as
        either a reply or a retweet. we'll also use case insensitive for the hashtag and case sensitive
        for the keywords
        """
        if self.query_type not in ["reply", "retweet", "both"]:
            raise ValueError(
                "Invalid query_type. Must be 'reply', 'retweet', or 'both'."
            )

        tweet_filter = {
            "reply": Q(
                (Q(reply_to_user_id=self.user_id) | Q(user_id=self.user_id))
                & Q(reply_to_user__isnull=False)
            ),
            "retweet": Q(
                (Q(retweet__user_id=self.user_id) | Q(user_id=self.user_id))
                & Q(retweet__isnull=False)
            ),
            "both": Q(
                (
                    Q(reply_to_user_id=self.user_id, reply_to_user__isnull=False)
                    | Q(user_id=self.user_id, reply_to_user__isnull=False)
                )
                | (
                    Q(retweet__user_id=self.user_id, retweet__isnull=False)
                    | Q(user_id=self.user_id, retweet__isnull=False)
                )
            ),
        }[self.query_type]

        tweets = Tweet.objects.filter(
            tweet_filter,
            lang__in=valid_languages,
        ).values("user_id", "text", "id")

        # keyword score is 0 if there are no contact tweets
        if not tweets:
            return {}

        keyword_scores = {}
        for tweet in tweets:
            user_id = tweet["user_id"]
            content = tweet["text"]
            number_of_matches = 0

            # Count phrase matches
            number_of_matches += content.count(self.phrase)

            # Count hashtag matches
            hashtags_in_tweet = Hashtag.objects.filter(
                tweet_id=tweet["id"], text__icontains=self.phrase
            ).count()
            number_of_matches += hashtags_in_tweet

            # keyword score is only 0 if there is no contact tweet
            keyword_score = 1 + log(number_of_matches + 1)
            keyword_scores[user_id] = keyword_score

        return keyword_scores

    def calculate_final_scores(self):
        """
        Final calculation based on the given values from the other three
        """
        interaction_scores = self.calculate_interaction_scores()
        hashtag_scores = self.calculate_hashtag_scores()
        keyword_scores = self.calculate_keywords_score()

        final_scores = {}
        for user_id in (
            set(interaction_scores) | set(hashtag_scores) | set(keyword_scores)
        ):
            interaction_score = interaction_scores.get(user_id, 0)
            hashtag_score = hashtag_scores.get(user_id, 1)
            keyword_score = keyword_scores.get(user_id, 0)
            final_score = interaction_score * hashtag_score * keyword_score
            if final_score > 0:
                final_scores[user_id] = round(final_score, 5)

        sorted_final_scores = sorted(
            final_scores.items(), key=lambda item: (-item[1], -item[0]), reverse=True
        )

        return sorted_final_scores


@api_view(["GET"])
def recommend_users(request):
    user_id = request.query_params.get("user_id")
    spec_type = request.query_params.get("type", "both")
    phrase = unquote(request.query_params.get("phrase", ""))
    hashtag = request.query_params.get("hashtag")

    if not user_id:
        return Response(
            {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_id = int(user_id)
    except ValueError:
        return Response(
            {"error": "user_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST
        )

    scorer = RankingScore(
        user_id=user_id,
        query_type=spec_type,
        phrase=phrase,
        hashtag=hashtag,
    )
    final_scores = scorer.calculate_final_scores()

    response_data = []

    for target_user_id, score in final_scores:
        user = TweetUser.objects.filter(id=target_user_id).first()
        if not user:
            continue

        tweet = (
            Tweet.objects.filter(
                Q(user_id=target_user_id)
                & (Q(reply_to_user_id=user_id) | Q(retweet__user_id=user_id)),
                lang__in=valid_languages,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        contact_tweet_text = " ".join(tweet.text) if tweet else ""

        response_data.append(
            {
                "user_id": user.id,
                "screen_name": user.screen_name,
                "description": user.description or " ",
                "contact_tweet_text": contact_tweet_text,
            }
        )

    formatted_response = "\n".join(
        f"{data['user_id']}\t{data['screen_name']}\t{data['description']}\t{data['contact_tweet_text']}"
        for data in response_data
    )

    return Response(formatted_response, content_type="text/plain")
