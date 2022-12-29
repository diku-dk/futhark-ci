# Copyright (C) 2018 GitHub, Inc. and contributors
# Copyright (C) 2018 Jacob Tomlinson

import os
import requests  # noqa We are just importing this to prove the dependency installed correctly

def main():
    permission = os.environ['INPUT_PERMISSION']
    # github_token = os.environ['GITHUB_TOKEN']
# 
    # header = {
    #     'Accept': 'application/vnd.github+json',
    #     'Authorization': f'Bearer {github_token}',
    #     'X-GitHub-Api-Version': '2022-11-28'
    # }

    # result = requests.api.post(url='https://api.github.com/users/WilliamDue/repos', header=header)

    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f :
            print(f'permission={permission}', file=f)
            print(f'result={os.environ.keys()}', file=f)


if __name__ == "__main__":
    main()
