# Self-hosted Runner
## Setting up a self-hosted runner
This guide assumes Linux is used.
### Setup
Go to the Futhark repository then navigate from Settings $\to$ Actions $\to$ Runners and then click the [New self-hosted runner](https://github.com/diku-dk/futhark/settings/actions/runners/new) button.

Inside here save the token `XXXXXXXXXXXXXXXXXXXXXXXXXXXXX` found in to configure box from the command `./config.sh --url https://github.com/diku-dk/futhark --token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX`.
Now put the [runner.py](runner.py) script into the folder where the runner will be stored. To setup and start the runner the script will be executed with the three following flags.
```
python3 runner.py --token {token} --name {name} --labels label0,label1,label2,...
``` 
An example setup is if a runner with a token `XXXXXXXXXXXXXXXXXXXXXXXXXXXXX`, name `test` and labels `cuda,opencl,multicore` would be.
```
python3 runner.py --token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX --name test --labels cuda,opencl,multicore
```
The name of the runner and its labels can be seen [here](https://github.com/diku-dk/futhark/settings/actions/runners) when it is setup. The idea with the labels is it makes one able to specify what benchmark the runner should perform by `runs-on: [label]` in the action workflow. Considering the last  example an example could be `runs-on: [cuda]`.

**When the runner is setup it will print the** `pid` **of the self-hosted runner process.** To check if the runner is active check [here](https://github.com/diku-dk/futhark/settings/actions/runners), on this page the runners status can be seen.

### Starting the runner
In case the self-hosted runner stops execute the command.
```
python3 runner.py --start
``` 
This command can also be used to restart the runner. When the runner has started the runner will put its log inside a log.txt file with the current date in the.

### Removal
When removing the runner go [here](https://github.com/diku-dk/futhark/settings/actions/runners) and click the three dots on the right side of the status of the runner that will be removed. Here the command can be found the command.`./config.sh remove --token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
Now execute the command with token from before.
```
python3 runner.py --remove XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
``` 

## Runner properties
Some important properties to note about the self-hosted runners is.
- The runner performs one job at a time.
- The runner token changes overtime.
- The runners can not be setup in the same folder because of `.runner`.
- Tokens can be reused for setup and removal.
- Working directory is not cleared from one run to the next. Example of this is when running the job:
    ```
    test:
        runs-on: test
        steps:
        - run: wget https://help.imgur.com/hc/article_attachments/115003454231/wow.gif
    ```
    will save wow.gif and when running the job again wow.gif.1 will be saved.
- The runner remembers the environment variables that were set when it was configured, not when it runs, in an .env file.