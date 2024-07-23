import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from multiprocessing import Pool
from recommend.models import Tweet, TweetUser, Hashtag
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_hashtag_batch(hashtags):
    with transaction.atomic():
        for tag in hashtags:
            user_id = tag.pop("user", None)
            tweet_id = tag.pop("tweet", None)

            user = TweetUser.objects.filter(id=user_id).first() if user_id else None
            tweet = Tweet.objects.filter(id=tweet_id).first() if tweet_id else None

            if user and tweet:
                Hashtag.objects.get_or_create(
                    user=user, tweet=tweet, defaults={"text": tag.get("text")}
                )
                logger.info(
                    f"Processed hashtag for user {user_id} and tweet {tweet_id}"
                )


class Command(BaseCommand):
    help = "Import tweets from a file to the database"

    def handle(self, *args, **kwargs):
        base_path = Path(settings.BASE_DIR)
        input_file_path = base_path / "filtered/valid_hashtags.txt"

        try:
            with open(input_file_path, "r") as file:
                hashtags = [json.loads(line.strip()) for line in file]

            num_processes = os.cpu_count() or 4
            chunk_size = max(1, len(hashtags) // num_processes)
            chunks = [
                hashtags[i : i + chunk_size]
                for i in range(0, len(hashtags), chunk_size)
            ]

            with Pool(processes=num_processes) as pool:
                pool.map(process_hashtag_batch, chunks)

            logger.info("All hashtags processed successfully.")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
