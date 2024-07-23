import json

from datetime import datetime as dt
from multiprocessing import Pool
from pathlib import Path

# Note: The language consideration is only for Query 2
# valid_languages = ["ar", "en", "fr", "in", "pt", "es", "tr", "ja"]

date_format = "%a %b %d %H:%M:%S %z %Y"


def get_tweet_objs(objs):
    """
    function to get all valid tweet objects for the database
    """
    tweets_ids = set()
    valid_twts = []

    for twt in objs:
        print(f"tweet line {len(valid_twts)}")

        tweet_obj = {
            "id": twt.get("id"),
            "user": twt["user"]["id"],
            "text": twt["text"],
            "reply_to_user": twt.get("in_reply_to_user_id"),
            "lang": twt["lang"],
            "created_at": twt["created_at"],
        }

        if twt.get("retweeted_status") is not None:
            tweet_obj["retweet"] = twt["retweeted_status"]["id"]

            if twt["retweeted_status"]["id"] not in tweets_ids:
                retweet_data = {
                    "id": twt["retweeted_status"]["id"],
                    "user": twt["retweeted_status"]["user"]["id"],
                    "text": twt["retweeted_status"]["text"],
                    "reply_to_user": twt["retweeted_status"]["in_reply_to_user_id"],
                    "lang": twt["retweeted_status"]["lang"],
                    "created_at": twt["retweeted_status"]["created_at"],
                }
                tweets_ids.add(retweet_data.get("id"))
                valid_twts.append(retweet_data)

        if twt["id"] not in tweets_ids:
            tweets_ids.add(tweet_obj.get("id"))
            valid_twts.append(tweet_obj)

    return valid_twts


def get_user_objs(objs):
    """
    function to get the user objects for the table
    """
    user_ids = set()
    valid_users = []

    for twt in objs:
        print(f"user line {len(valid_users)}")

        user_info = {
            "id": twt["user"]["id"],
            "screen_name": twt["user"]["screen_name"],
            "description": twt["user"]["description"],
            "lang": twt["user"]["lang"],
            "created_at": twt["user"]["created_at"],
            "updated_at": twt["created_at"],
        }

        if twt.get("retweeted_status") is not None:
            retweet_data = {
                "id": twt.get("retweeted_status").get("user").get("id"),
                "screen_name": twt.get("retweeted_status")
                .get("user")
                .get("screen_name"),
                "description": twt.get("retweeted_status")
                .get("user")
                .get("description"),
                "lang": twt.get("retweeted_status").get("user").get("lang"),
                "created_at": twt.get("retweeted_status").get("user").get("created_at"),
                "updated_at": twt["retweeted_status"]["created_at"],
            }

            if retweet_data.get("id") not in user_ids:
                user_ids.add(retweet_data.get("id"))
                valid_users.append(retweet_data)

            # since the data is in chronological order and we are using the
            # created datetime to check for updated info, we'll add an else condition
            # to do just that
            else:
                existing_data = [
                    data
                    for data in valid_users
                    if data.get("id") == retweet_data.get("id")
                ]
                datetime_2 = dt.strptime(retweet_data["updated_at"], date_format)
                datetime_1 = dt.strptime(
                    existing_data[0].get("updated_at"), date_format
                )

                if datetime_2 > datetime_1:
                    # update the object in place
                    existing_data[0].update(retweet_data)

        if user_info.get("id") not in user_ids:
            user_ids.add(user_info.get("id"))
            valid_users.append(user_info)

        # since the data is in chronological order and we are using the
        # created datetime to check for updated info, we'll add an else condition
        # to do just that
        else:
            existing_data = [
                data for data in valid_users if data.get("id") == user_info.get("id")
            ]
            datetime_2 = dt.strptime(user_info["updated_at"], date_format)
            datetime_1 = dt.strptime(existing_data[0].get("updated_at"), date_format)

            if datetime_2 > datetime_1:
                # update the object in place
                existing_data[0].update(user_info)

    return valid_users


def get_hashtags(objs):
    """
    function to get all valid hashtags in relation to the user id for the database
    """
    twts_ids = set()
    valid_hashtags = []

    for twt in objs:
        print(f" hashtag line {len(valid_hashtags)}")

        twt_user_id = twt.get("user").get("id")
        twt_obj_id = twt.get("id")

        if (twt_user_id, twt_obj_id) not in twts_ids:
            for txt in twt.get("entities").get("hashtags"):
                hashtag_obj = {
                    "user": twt_user_id,
                    "tweet": twt_obj_id,
                    "text": txt["text"],
                }
                valid_hashtags.append(hashtag_obj)
            twts_ids.add(
                (twt_user_id, twt_obj_id)
            )  # this should help with occurences right?

        tweet_retweet = twt.get("retweeted_status")
        if tweet_retweet is not None:
            tweet_retweet_id = tweet_retweet.get("id")
            tweet_retweet_user_id = tweet_retweet.get("user").get("id")
            if (tweet_retweet_user_id, tweet_retweet_id) not in twts_ids:
                for rtxt in twt.get("retweeted_status").get("entities").get("hashtags"):
                    rt_hashtag = {
                        "user": tweet_retweet_user_id,
                        "tweet": tweet_retweet_id,
                        "text": rtxt["text"],
                    }
                    valid_hashtags.append(rt_hashtag)
                twts_ids.add((tweet_retweet_user_id, tweet_retweet_id))
                # twts_ids.add(f"{rt_hashtag.get('user')}-{rt_hashtag.get('tweet')}")

    return valid_hashtags


def process_lines(lines):
    unique_ids = set()
    valid_objects = []

    for line in lines:
        print(f"process line {len(valid_objects)}")
        try:
            obj = json.loads(line.strip())
            obj_id = obj.get("id")
            obj_id_str = obj.get("id_str")

            obj_user = obj.get("user")
            obj_user_id = obj_user.get("id")
            obj_user_id_str = obj_user.get("id_str")

            obj_created_at = obj.get("created_at")
            obj_txt = obj.get("text")
            obj_entities = obj.get("entities")
            obj_hashtags = obj_entities.get("hashtags")

            if obj_id is None and obj_id_str is None:
                continue

            if obj_user_id is None and obj_user_id_str is None:
                continue

            if obj_txt is None or obj_txt == "":
                continue

            if obj_created_at is None:
                continue

            if obj_hashtags is None or len(obj_hashtags) == 0:
                continue

            obj_identity = obj_id or int(obj_id_str)  # if obj_id_str else None

            if obj_identity is not None and obj_identity not in unique_ids:
                unique_ids.add(int(obj_identity))
                valid_objects.append(obj)
        except (json.JSONDecodeError, KeyError):
            continue

    return valid_objects


def process_file(
    input_file, twt_output_file, usr_output_file, hshtags_out_file, num_processes
):
    with open(input_file, "r") as file:
        lines = file.readlines()

    # Split lines into chunks
    chunk_size = len(lines) // num_processes
    chunks = [lines[i : i + chunk_size] for i in range(0, len(lines), chunk_size)]

    # filter for malformed and dupicate
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_lines, chunks)

    # double checking
    unique_ids = set()
    valid_objects = []
    for result in results:
        for obj in result:
            obj_id = obj["id"]
            if obj_id not in unique_ids:
                unique_ids.add(obj_id)
                valid_objects.append(obj)

    # anticipating changes
    tweets_chunk_size = len(valid_objects) // num_processes
    tweets_chunks = [
        valid_objects[i : i + tweets_chunk_size]
        for i in range(0, len(valid_objects), tweets_chunk_size)
    ]

    # filter for tweet data
    with Pool(processes=num_processes) as pool:
        valid_tweets_objects = pool.map(get_tweet_objs, tweets_chunks)

    # filter for user data
    with Pool(processes=num_processes) as pool:
        valid_user_objects = pool.map(get_user_objs, tweets_chunks)

    # filer for hashtags
    with Pool(processes=num_processes) as pool:
        valid_hashtag_objects = pool.map(get_hashtags, tweets_chunks)

    # write results to files
    # tweet result
    # flattenout the list
    valid_twt_list = [obj for sublist in valid_tweets_objects for obj in sublist]
    with open(twt_output_file, "w") as tweet_file:
        for obj in valid_twt_list:
            tweet_file.write(json.dumps(obj) + "\n")

    # user result
    # flattenout the list
    valid_usr_list = [obj for sublist in valid_user_objects for obj in sublist]
    with open(usr_output_file, "w") as user_file:
        for obj in valid_usr_list:
            user_file.write(json.dumps(obj) + "\n")

    # hashtags result
    # flatten out thelist
    valid_hashtag_list = [obj for sublist in valid_hashtag_objects for obj in sublist]
    with open(hshtags_out_file, "w") as hashtag_file:
        for obj in valid_hashtag_list:
            hashtag_file.write(json.dumps(obj) + "\n")


if __name__ == "__main__":
    base_path = Path(__file__).resolve(strict=True).parent

    input_file_path = f"{base_path}/challenge/datasets/query2_ref.txt"
    twt_output_file = f"{base_path}/filtered/valid_tweet_objects.txt"
    usr_output_file = f"{base_path}/filtered/valid_usr_obj.txt"
    hshtags_out_file = f"{base_path}/filtered/valid_hashtags.txt"

    num_processes = 4

    process_file(
        input_file_path,
        twt_output_file,
        usr_output_file,
        hshtags_out_file,
        num_processes,
    )
