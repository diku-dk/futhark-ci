# Copyright (C) 2018 GitHub, Inc. and contributors
# Copyright (C) 2018 Jacob Tomlinson

import os
import requests  # noqa We are just importing this to prove the dependency installed correctly
from github import Github

def main():
    permission = os.environ["INPUT_MYINPUT"]
    github_token = os.environ["GITHUB_TOKEN"]

    g = Github(github_token)

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print(f"myOutput={permission}", file=f)


if __name__ == "__main__":
    main()
