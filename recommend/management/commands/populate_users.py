import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from multiprocessing import Pool
from recommend.models import TweetUser
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%a %b %d %H:%M:%S %z %Y")


def process_user_batch(users):
    with transaction.atomic():
        for usr in users:
            if usr.get("created_at"):
                usr["created_at"] = parse_datetime(usr["created_at"])

            if usr.get("updated_at"):
                usr["updated_at"] = parse_datetime(usr["updated_at"])

            TweetUser.objects.update_or_create(id=usr.get("id"), defaults=usr)
            logger.info(f"Processed user ID: {usr.get('id')}")


class Command(BaseCommand):
    help = "Import users from a file to the database"

    def handle(self, *args, **kwargs):
        base_path = Path(settings.BASE_DIR)
        input_file_path = base_path / "filtered/valid_usr_obj.txt"

        try:
            with open(input_file_path, "r") as file:
                users = [json.loads(line.strip()) for line in file]

            num_processes = os.cpu_count() or 4
            chunk_size = max(1, len(users) // num_processes)
            chunks = [
                users[i : i + chunk_size] for i in range(0, len(users), chunk_size)
            ]

            with Pool(processes=num_processes) as pool:
                pool.map(process_user_batch, chunks)

            logger.info("All users processed successfully.")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
