import pandas as pd
from pathlib import Path
work_dir = Path('/Users/yunchaewon/gardeners/')
repo_path = work_dir / 'comments'
dup_path = work_dir / 'duplicates'

for file in list(repo_path.glob('*.json')):
    dup_file = dup_path / file.parts[-1]
    # print(file)
    # print(dup_file)
    if dup_file.exists():
        df1 = pd.read_json(file)
        df2 = pd.read_json(dup_file)
        if len(df1)!=len(df2):
            print(file)
        # df3 = df1.merge(df2,how='outer')
        # print(f'df3:{len(df3)}')
        # for file in files:
#     if os.path.isfile(file)
#
