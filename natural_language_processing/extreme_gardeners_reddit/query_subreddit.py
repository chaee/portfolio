import argparse
import calendar
import datetime
import os
import time
from datetime import date
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import *
from pmaw import PushshiftAPI
import praw

# sns.set_theme(style="whitegrid")
# pd.set_option('max_colwidth', 500)
# pd.set_option('max_columns', 50)

api = PushshiftAPI()

# TODO create script for checking duplicates to identify missing window?


def get_daily_response(dir, next_posix, retries=5):
    """
    send request to pushshift api, add formated datetime column in df, write into a json file
    :param dir: path to save json files
    :param next_posix:
    :return: the earliest posix time among the response; will serve as starting point for the next call
    """

    limit = 100
    # TODO it limits the output size more or less to 3mb....?
    # TODO how to scrape more when the comments are more densely populated? reduce posix gap?

    last_timestamp = next_posix
    next_date = date.fromtimestamp(next_posix)
    #next_date = since_date + relativedelta(hours=+1)
    #until_date = datetime.fromtimestamp(next_posix)

    old_path = os.path.join(dir, f'{str(next_date) + "_" + str(next_posix)}.json')
    if os.path.exists(old_path):
        print(f'{str(next_date) + "_" + str(next_posix)}.json was queried before')

    else:
        print(f'Submissions until :{next_date}')
        # print(f'Submissions until :{until_date}')
        print(f'current posix:{next_posix}')

        for retry in range(retries):
            try:
                print("trying")
                # raise Exception('foo')
                api_request_generator = list(api.search_comments(subreddit='aww',
                                                         before=next_posix,
                                                         # after=since_posix,
                                                         safe_exit=True,
                                                         mem_safe=True,
                                                         limit=limit,
                                                         until=next_posix
                                                         ))
                break
            except Exception as e:
                print(f'API request failed. Try: {retry+1}/{retries}')
                print(f'error: {e}')
                time.sleep(10)
        else:
            raise Exception("Too many retries. Existing")
        # TODO why no deeper nested comments?
        # print(api.metadata_.get('shards'))

        if len(api_request_generator):
            submissions = pd.DataFrame([submission for submission in api_request_generator])
            last_timestamp = submissions['created_utc'].min()
            print(last_timestamp-next_posix)
            print(f'next_posix:{last_timestamp}')
            print(f'next date begins with: {date.fromtimestamp(last_timestamp)}')
            submissions['date'] = pd.to_datetime(submissions['created_utc'], utc=True, unit='s')

            # TODO merge files into bigger sized files
            submissions.to_json(f'{dir}/{str(next_date) + "_" + str(last_timestamp)}.json', index=True)
            print(f'Finished: {dir}/{str(next_date)+ "_" + str(last_timestamp)}.json')
        else:
            print("No response from API-----!")
            # TODO add to log to figure out what's missing
            # TODO try move just 10 items and check if next 100 contains overlapping 90 items
            # TODO separate script to get list of directory/file glob pattern
            #  takes only the date and unique ids and show the graph
    return int(last_timestamp)


def find_earliest(result_dir):
    """
    check the filenames in the result folder and find the earliest unix time
    :param result_dir:
    :return:
    """
    files = list(Path(result_dir).glob('*.json'))
    if files:
        posix_list = list()
        for file in files:
            posix_list.append(str(file.parts[-1]).split('_')[-1][:-5])  # make list of posix dates from file names

        end_posix = int(sorted(posix_list)[0])  # find the earliest posix
        end_date = date.fromtimestamp(end_posix)
    else:
        end_date = datetime.date(2016, 1, 1) # TODO remove hardcoded date
    return end_date


def shift_timeframes(args):
    """
    calls function for API call with the modified time frames
    :param args: user input for setting target period or check existing files
    :return: nothing; just calls get_daily_response in the loop
    """
    work_dir = os.getcwd()
    res_dir = os.path.join(work_dir, args.path)

    if os.path.isdir(res_dir):
        print(f'{res_dir} already exists!')
    os.makedirs(res_dir, exist_ok=True)

    if args.time:
        end_posix = int(args.time)
        end_date = date.fromtimestamp(end_posix)
    elif args.date:
        dates = args.date.split('-')
        end_date = datetime.date(int(dates[0]), int(dates[1]), int(dates[2]))
    else:
        end_date = find_earliest(res_dir)

    start_date = datetime.date(2016, 1, 1) # TODO hardcoded date for the earliest date during the target period
    # while ((end_date - next_date) > datetime.timedelta(days=1)):

    latest_posix = calendar.timegm(end_date.timetuple())  # start at the latest date of the target period
    earliest_posix = calendar.timegm(start_date.timetuple())  # continue till the earliest date of the target period

    while True:
        # next_date = start_date + relativedelta(days=+1)
        timer_start = time.process_time()
        next_posix = get_daily_response(res_dir, latest_posix)
        if next_posix == latest_posix:
            latest_posix = next_posix - 200  # TODO find a better interval?
        else:
            latest_posix = next_posix
        print(f'next posix:{next_posix}')
        print(time.process_time() - timer_start)

        if next_posix <= earliest_posix:
            print(f'{next_posix} - {earliest_posix}')
            print(next_posix < earliest_posix)
            print(date.fromtimestamp(next_posix))
            print(date.fromtimestamp(earliest_posix))

            print('finished!')
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='p: name the folder to save comments // '
                                                 'd: input the last date of the target period with hyphens')
    parser.add_argument('-p', '--path', default='other_comments/missing_aww')
    parser.add_argument('-d', '--date', default='2016-09-01')
    parser.add_argument('-t', '--time')

    p_args = parser.parse_args()
    # with cProfile.Profile() as pr:
    shift_timeframes(p_args)
    # pr.dump_stats('stats.bin')
