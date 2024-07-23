from datetime import UTC, datetime
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from ..models import Tweet, Hashtag, TweetUser


class RecommendUsersIntegrationTestCase(APITestCase):
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
            description="Hello test 2",
            lang="en",
            updated_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        self.user_3 = TweetUser.objects.create(
            id=5000,
            screen_name="user3",
            description="Hello test 3",
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
            lang="ar",
            created_at=datetime.now(UTC),
        )

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
            tweet=self.tweet_1, user=self.user_1, text="Mone", is_popular=True
        )
        Hashtag.objects.create(
            tweet=self.tweet_2, user=self.user_3, text="cloud", is_popular=False
        )

        self.client = APIClient()

    def test_recommend_users(self):
        url = reverse("recommend_users")
        response = self.client.get(
            url,
            {
                "user_id": self.user_1.id,
                "type": "both",
                "phrase": "Hello",
                "hashtag": "test",
            },
        )

        self.assertEqual(response["Content-Type"], "text/plain")

        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        Tweet.objects.all().delete()
        Hashtag.objects.all().delete()
        TweetUser.objects.all().delete()
