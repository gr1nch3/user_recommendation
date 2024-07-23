import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from multiprocessing import Pool
from recommend.models import Tweet, TweetUser
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%a %b %d %H:%M:%S %z %Y")


def process_tweet_batch(tweets):
    with transaction.atomic():
        for twt in tweets:
            if twt.get("created_at"):
                twt["created_at"] = parse_datetime(twt.get("created_at"))

            user_id = twt.pop("user", None)
            reply_to_usr = twt.pop("reply_to_user", None)
            retweet = twt.pop("retweet", None)

            twt["user"] = (
                TweetUser.objects.filter(id=user_id).first() if user_id else None
            )
            twt["reply_to_user"] = (
                TweetUser.objects.filter(id=reply_to_usr).first()
                if reply_to_usr
                else None
            )
            twt["retweet"] = (
                Tweet.objects.filter(id=retweet).first() if retweet else None
            )

            Tweet.objects.update_or_create(id=twt.get("id"), defaults=twt)
            logger.info(f"Processed tweet ID: {twt.get('id')}")


class Command(BaseCommand):
    help = "Import tweets from a file to the database"

    def handle(self, *args, **kwargs):
        base_path = Path(settings.BASE_DIR)
        input_file_path = base_path / "filtered/valid_tweet_objects.txt"

        try:
            with open(input_file_path, "r") as file:
                tweets = [json.loads(line.strip()) for line in file]

            num_processes = os.cpu_count() or 4
            chunk_size = max(1, len(tweets) // num_processes)
            chunks = [
                tweets[i : i + chunk_size] for i in range(0, len(tweets), chunk_size)
            ]

            with Pool(processes=num_processes) as pool:
                pool.map(process_tweet_batch, chunks)

            logger.info("All tweets processed successfully.")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
