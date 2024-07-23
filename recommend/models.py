from django.db.models import (
    CASCADE,
    SET_NULL,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    TextField,
)


# Create your models here.
class TweetUser(Model):
    screen_name = CharField(max_length=255)
    description = TextField(null=True)
    # length updated to 50, my fault for wanting to use a lang on the user
    lang = CharField(max_length=50)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    def __str__(self):
        return self.screen_name


class Tweet(Model):
    user = ForeignKey(TweetUser, on_delete=CASCADE)
    text = TextField()
    reply_to_user = ForeignKey(
        TweetUser, null=True, on_delete=CASCADE, related_name="reply_to_user"
    )
    retweet = ForeignKey(
        "self",
        null=True,
        on_delete=SET_NULL,
        related_name="retweets",
    )
    lang = CharField(max_length=10)
    created_at = DateTimeField()

    def __str__(self):
        return self.text


class Hashtag(Model):
    user = ForeignKey(TweetUser, null=False, on_delete=CASCADE)
    tweet = ForeignKey(Tweet, null=False, on_delete=CASCADE)
    text = CharField()
    is_popular = BooleanField(default=False)

    class Meta:
        # to ensure uniqueness and avoid overiding case of multiple hashtags on the same tweet
        unique_together = ("user", "tweet", "text")

    def __str__(self):
        return self.text
