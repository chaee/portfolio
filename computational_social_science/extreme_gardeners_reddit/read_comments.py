import json
import os
import argparse
from pathlib import Path

import pandas as pd

from pprint import pprint
from pmaw import PushshiftAPI

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_seq_items', None)

api = PushshiftAPI()


def sanity_check(dir):
    files = Path(dir).glob('*.json')
    for idx, file in enumerate(files):
        print(f'processing {file}...')
        df = pd.read_json(file)
        df_len = len(df)
        unique_len = len(df.id.unique())
        print(f'total # - unique # = {df_len} - {unique_len} = {df_len-unique_len}')


def union_dates(dup_date, df, dup_dir):
    """
    compare df of certain date with date files in agg_dir
    :param dup_date: date where dup_file exists in dup_dir
    :param df: aggregated comments from certain date
    :param agg_dir: path where aggregated daily files are
    :return: df that is union of date in dup_dir and df
    """
    small_files = list(Path(dup_dir).glob('*.json'))
    date_dict = dict()
    for file in small_files:
        date = file.parts[-1].split('_')[0]
        if date in date_dict.keys():
            date_dict[date].append(file)
        else:
            date_dict[date] = [file]

    for small_file in date_dict[dup_date]:
        small_df = pd.read_json(small_file)
        df = pd.concat([df, small_df], axis=0, ignore_index=True)
    # print(f'before drop dup:{len(df)}')
    df = df.drop_duplicates()
    # print(f'after drop dup:{len(df)}')
    return df


def merge_comment_files(f_dir, agg_dir):
    # TODO how to combine files with the same filename but maybe different content inside?
    # TODO should query multiple times + union the results to minimize missing windows?
    small_files = list(Path(f_dir).glob('*.json'))
    date_dict = dict()

    for file in small_files:
        date = file.parts[-1].split('_')[0]
        if date in date_dict.keys():
            date_dict[date].append(file)
        else:
            date_dict[date] = [file]

    complete_list = list()
    for date, fnames in date_dict.items(): # TODO sorted?
        df_list = list()
        for fname in fnames:
            df_list.append(pd.read_json(fname))
        complete_list += df_list
        result = pd.concat(df_list)
        result.reset_index(inplace=True)
        '''
        if date in dup_dates:
            result = union_dates(date, result, dup_path)
            print(f'{date} duplicates removed!')
        '''
        result.to_json(os.path.join(agg_dir, f'{date}.json'))
        print(f'{date} merged!')

    dates = sorted(list(date_dict.keys()))
    single_file = pd.concat(complete_list)
    single_file.reset_index(inplace=True)
    single_file.to_json(os.path.join(agg_dir, f'{dates[0]}_{dates[-1]}.json'))
    single_file.to_csv(os.path.join(agg_dir, f'{dates[0]}_{dates[-1]}.csv'))



def extract_authors(json_file):
    sr_dict = dict()
    df = pd.read_json(json_file)
    author = str(json_file).split('/')[-1][:-5]
    # print(author)
    subreddits = pd.Series(df.subreddit.unique())
    sr_dict[author] = list(df.subreddit.unique())
    subreddits = set(list(subreddits) + sr_dict[author])
    print(subreddits)
    new = pd.DataFrame(columns=sr_dict.keys(), index=list(subreddits))

    new = pd.DataFrame({'author': author,
                       'srd': sr_dict[author]})
    subreddits = pd.concat([subreddits, new], axis=0, ignore_index=True)

    new = df[["author", "subreddit", "title","created_utc", "domain", "id",  "selftext"]]
    subreddits = pd.concat([subreddits, new], axis=0, ignore_index=True)

    subreddit_counts = subreddits.groupby('subreddit')['author'].count()
    print(subreddit_counts.sort_values(ascending=False, inplace=True))
    subreddit_counts.to_csv('other_subreddits_count.csv', index=True)

    subreddits.to_json('other_subreddits.json', index=True)


def read_summary(fname):
    df = pd.read_json(fname)
    print(df.head())  # there are duplicates

    #sorted_subreddit_counts = subreddit_counts.sort_values(by='author', ascending=False, inplace=True).value_counts()
    #print(sorted_subreddit_counts)
    #print(subreddits.groupby('subreddit').count())
    #print(subreddits.groupby('srd'))#['The_Donald'])
    #subreddits.srd.value_counts().plot(kind='bar')
    #print(subreddits.srd.value_counts())


def check_final_csv(csv_path):
    compact_cols = ['date', 'body', 'author', 'id']
    csv_fname = list(Path(csv_path).glob('*.csv'))[0]

    df = pd.read_csv(csv_fname)
    print(len(df))
    print(df.columns)


def make_dup_dates(dup_dir, agg_dir):
    dup_files = list(Path(dup_dir).glob('*.json'))
    dates = list()

    for file in dup_files:
        dats = file.parts[-1].split('_')[0]
        dates.append(date)

    return dates


def simple_merge(dir, folder_name):
    files = Path(dir).glob('*.json')
    # comments_only = list() just for comments
    compact_cols = ['date', 'body', 'author', 'id']
    combined_df = pd.DataFrame()
    for idx, file in enumerate(files):
        print(f'processing {idx}th file!')
        df = pd.read_json(file)
        small_df = df[compact_cols]
        # comments_only.append(df.body) just for comments
        combined_df = pd.concat([combined_df, small_df], axis=0, ignore_index=True)
    # result = pd.concat(comments_only)
    # result.reset_index(inplace=True)


    # result.to_csv(os.path.join(dir, f'{folder_name}.csv')) just for comments
    combined_df.to_csv(os.path.join(dir, f'{folder_name}.csv'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='p: name the folder where comments are')
    parser.add_argument('-p', '--path', default='new_comments')
    parser.add_argument('-d', '--duplicate_path', default='duplicate_posix')
    args = parser.parse_args()
    '''
    work_dir = os.getcwd()
    files = os.path.join(work_dir, args.path)
    agg_path = os.path.join(work_dir, 'others_aggregated_daily')
    os.makedirs(agg_path, exist_ok=True)
    dup_path = os.path.join(work_dir, args.duplicate_path)

    dup_dates = make_dup_dates(dup_path, agg_path)
    '''
    #merge_comment_files(files, agg_path)
    simple_merge(args.path, 'the_Donald')
    # sanity_check(agg_path)
    # check_final_csv(agg_path)


#read_summary('other_subreddits.json')
