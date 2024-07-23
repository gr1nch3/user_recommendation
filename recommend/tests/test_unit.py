from datetime import UTC, datetime
from django.test import TestCase
from ..models import Tweet, Hashtag, TweetUser
from ..views import RankingScore


class RankingScoreUnitTest(TestCase):
    def setUp(self):
        # Create test users
        self.user_1 = TweetUser.objects.create(
            id=3000,
            screen_name="user1",
            description="Hello test 1",
            lang="en",
            updated_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        self.user_2 = TweetUser.objects.create(
            id=4000,
            screen_name="user2",
            description="Hello test 1",
            lang="en",
            updated_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        self.user_3 = TweetUser.objects.create(
            id=5000,
            screen_name="user3",
            description="Hello test 1",
            lang="en",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Create test tweets
        self.tweet_1 = Tweet.objects.create(
            user=self.user_1,
            text="Hello world",
            reply_to_user=self.user_2,
            lang="en",
            created_at=datetime.now(UTC),
        )
        self.tweet_2 = Tweet.objects.create(
            user=self.user_1,
            text="Another tweet",
            retweet=None,  # will update later
            lang="ja",
            created_at=datetime.now(UTC),
        )
        self.tweet_3 = Tweet.objects.create(
            user=self.user_1,
            text="Hello Test",
            reply_to_user=self.user_1,
            lang="es",
            created_at=datetime.now(UTC),
        )
        self.tweet_4 = Tweet.objects.create(
            user=self.user_2,
            text="Another re tweet",
            retweet=None,  # will update later
            lang="ar",
            created_at=datetime.now(UTC),
        )

        # Update retweet fields with Tweet instances
        self.tweet_2.retweet = self.tweet_1
        self.tweet_2.save()
        self.tweet_4.retweet = self.tweet_3
        self.tweet_4.save()

        # Create test hashtags
        Hashtag.objects.create(
            tweet=self.tweet_1, user=self.user_1, text="test", is_popular=False
        )
        Hashtag.objects.create(
            tweet=self.tweet_2, user=self.user_1, text="example", is_popular=False
        )
        Hashtag.objects.create(
            tweet=self.tweet_3, user=self.user_3, text="hello", is_popular=False
        )
        Hashtag.objects.create(
            tweet=self.tweet_4, user=self.user_2, text="code", is_popular=False
        )
        Hashtag.objects.create(
            tweet=self.tweet_1, user=self.user_1, text="Money", is_popular=True
        )
        Hashtag.objects.create(
            tweet=self.tweet_2, user=self.user_3, text="cloud", is_popular=False
        )

    def test_calculate_interaction_scores(self):
        scorer = RankingScore(
            user_id=3000,
            query_type="both",
            phrase="Hello",
            hashtag="test",
        )
        interaction_scores = scorer.calculate_interaction_scores()
        self.assertEqual(
            interaction_scores, {4000: 1.3862943611198906, 3000: 1.0986122886681098}
        )

    def test_calculate_hashtag_scores(self):
        scorer = RankingScore(
            user_id=4000,
            query_type="both",
            phrase="Hello",
            hashtag="test",
        )
        hashtag_scores = scorer.calculate_hashtag_scores()
        self.assertEqual(hashtag_scores, {4000: 1.0})

    def test_calculate_keywords_score(self):
        scorer = RankingScore(
            user_id=5000,
            query_type="both",
            phrase="Hello",
            hashtag="test",
        )
        keyword_scores = scorer.calculate_keywords_score()
        self.assertEqual(keyword_scores, {})

    def tearDown(self):
        Tweet.objects.all().delete()
        Hashtag.objects.all().delete()
        TweetUser.objects.all().delete()
