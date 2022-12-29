# Copyright (C) 2018 GitHub, Inc. and contributors
# Copyright (C) 2018  Jacob Tomlinson

import os
import requests  # noqa We are just importing this to prove the dependency installed correctly
import yamllint

def main():
    yaml_path = os.environ["INPUT_MYINPUT"]

    my_output = f"Hello {yaml_path}"

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print("{0}={1}".format("myOutput", my_output), file=f)


if __name__ == "__main__":
    main()
