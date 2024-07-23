import os
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from multiprocessing import Pool, cpu_count
from recommend.models import Hashtag
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_hashtag_batch(hashtags):
    with transaction.atomic():
        for tag in hashtags:
            hashtag_objects = Hashtag.objects.filter(text__iexact=tag)
            if hashtag_objects.exists():
                hashtag_objects.update(is_popular=True)
                logger.info(f"Updated 'is_popular' for hashtag: {tag}")
            else:
                Hashtag.objects.create(text=tag, is_popular=True)
                logger.info(f"Created new hashtag: {tag} and set 'is_popular'")


class Command(BaseCommand):
    help = "Import tweets from a file to the database"

    def handle(self, *args, **kwargs):
        base_path = Path(settings.BASE_DIR)
        input_file_path = base_path / "challenge/datasets/popular_hashtags.txt"

        try:
            with open(input_file_path, "r") as file:
                hashtags = [line.strip() for line in file]

            num_processes = cpu_count() or 4
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
