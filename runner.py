#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 9), "Use Python 3.9 or newer."

import os
import socket
import optparse
import datetime
import shutil
import subprocess
import time
import signal
import json
import shlex
from typing import Optional


# The default flags depending on the hostname.
DEFAULT_SETTINGS = {
    'futharkhpa01fl.unicph.domain': {
        'name': 'futhark01',
        'labels': 'A100,cuda,opencl,multicore',
    },
    'futharkhpa02fl.unicph.domain': {
        'name': 'futhark02',
        'labels': 'MI100,opencl,multicore',
    },
    'futharkhpa03fl.unicph.domain': {
        'name': 'futhark03',
        'labels': 'A100,cuda,opencl,multicore',
    },
}

# These are the commands used for installing the self-hosted runner. You may wish to update these
# commands with commands from the download box on the website.
# https://github.com/{organization}/{repository}/settings/actions/runners/new
version='2.300.2'
shasum='ed5bf2799c1ef7b2dd607df66e6b676dff8c44fb359c6fedc9ebf7db53339f0c'
INSTALLATION = \
f'''curl -o actions-runner-linux-x64-{version}.tar.gz -L https://github.com/actions/runner/releases/download/v{version}/actions-runner-linux-x64-{version}.tar.gz
echo "{shasum} actions-runner-linux-x64-{version}.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-{version}.tar.gz
rm actions-runner-linux-x64-{version}.tar.gz'''

# The folder where the runner files are stored.
RUNNER_FOLDER = 'actions-runner'

def replace_home(env: dict, new_home: str):
    env = env.copy()
    old_home = env['HOME']

    for key, val in env.items():
        env[key] = val.replace(old_home, new_home)
    
    return env

# The enviroment variables that will be used in each process.
ENV = replace_home(os.environ, os.path.join(os.getcwd(), RUNNER_FOLDER))


class Chdir:
    '''
    A class for using with statements for changing working directory and getting back to the working
    directory from when the object was instantiated.
    '''

    def __init__(self, path) -> None:
        '''
        Parameters
        ----------
        path : str
            The path the working directory will be changed to.
        '''

        self._path = path
        self._old_path = os.getcwd()


    def __enter__(self):
        '''
        When inside the scope of the with statement then the path is the one given in the
        constructor.
        '''
        os.chdir(self._path)


    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Goes back to the working directory from when the object was instantiated.
        '''
        os.chdir(self._old_path)


def get_name() -> Optional[str]:
    '''
    Retrieves the name found in .runner and if not possible then None is returned.
    
    Returns
    -------
    Optional[str]
        The name ofthe runner or None if the name does not exist.
    '''

    path = os.path.join('.runner')
    if not os.path.exists(path):
        return None
    fp = open(path, encoding='utf-8-sig', mode='r')
    return json.load(fp).get('agentName')


def is_any_none_flags(flags: dict[str, Optional[str]]) -> Optional[Exception]:
    '''
    This function checks if any flags are none and reports an error asking for the last arguments
    if sol.

    Parameters
    ----------
    flags : dict[str, Optional[str]]
        The flags which have been passed to the installation script.
    
    Returns
    -------
    bool
        True if the flags were valid otherwise false.
    Optional[Exception]
        None if the flags were valid otherwise a corresponding error.
    '''
    if any(map(lambda opt: opt is None, flags.values())):
        missing_arg_pairs = filter(lambda pair: pair[1] is None, flags.items())
        missing_args = ', '.join(map(lambda pair: pair[0], missing_arg_pairs))
        return Exception(f'Missing arguments: Please specify {missing_args}.')

    return None


def is_all_none_flags(flags: dict[str, Optional[str]]) -> Optional[Exception]:
    '''
    Checks if all the flags are set to None.

    Parameters
    ----------
    flags : dict[str, Optional[str]]
        The flags which have been passed to the installation script.
    
    Returns
    -------
    bool
        True if the flags were valid otherwise false.
    Optional[Exception]
        None if the flags were valid otherwise a corresponding error.
    '''

    if any(map(lambda opt: opt is not None, flags.values())):
        passed_arg_pairs = filter(lambda pair: pair[1] is not None, flags.items())
        passed_args = ', '.join(map(lambda pair: pair[0], passed_arg_pairs))
        return Exception(f'Too many arguments: Do not specify {passed_args} when ' +
        'using the start flag.')

    return None


def get_flags() -> dict[str, str]:
    '''
    Retrieves the flags given by the user and returns them as a dictionary.

    Example Output:
    {
        'token': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        'url': 'https://github.com/diku-dk/futhark',
        'name': 'runner',
        'labels': 'cuda,opencl,multicore'
    }
    
    Returns
    -------
    dict[str, str]
        The flags given by the user as a dictionary.
    '''

    parser = optparse.OptionParser()
    parser.add_option('-t', '--token', dest='token', type='string',
                      help='the runner TOKEN.', metavar='TOKEN')
    parser.add_option('-u', '--url', dest='url', type='string',
                      help='the URL to the repository the runner is used for. ' + 
                      'Defaults to "https://github.com/diku-dk/futhark"', metavar='URL')
    parser.add_option('-n', '--name', dest='name', type='string',
                      help='the NAME of the runner.', metavar='NAME')
    parser.add_option('-l', '--labels', dest='labels', type='string',
                      help='the LABELS the runner should have.', metavar='LABELS')
    parser.add_option('-s', '--start', action="store_true", dest="start", default=False,
                      help='If the runner should START.', metavar='START')
    parser.add_option('-k', '--kill', action="store_true", dest="kill", default=False,
                      help='If the runner should be stopped.', metavar='KILL')
    parser.add_option('-r', '--remove', dest="remove",
                      help='the token belonging to the runner that will be REMOVEd.', metavar='REMOVE')
    (flags, _) = parser.parse_args()
    flags = flags.__dict__
    
    if flags.get('start'):
        start = flags.pop('start')

        error = is_all_none_flags(flags)
        if error is not None:
            raise error
        
        flags = {'start': start}
        return flags
    
    flags.pop('start')

    if flags.get('kill'):
        kill = flags.pop('kill')

        error = is_all_none_flags(flags)
        if error is not None:
            raise error
        
        flags = {'kill': kill}
        return flags
    
    flags.pop('kill')

    if flags.get('remove') is not None:
        remove = flags.pop('remove')

        error = is_all_none_flags(flags)
        if error is not None:
            raise error

        flags = {'remove': remove}
        return flags
    
    remove = flags.pop('remove')
    
    if flags.get('url') is None:
        flags['url'] = 'https://github.com/diku-dk/futhark'

    hostname = socket.gethostname()
    settings = DEFAULT_SETTINGS.get(hostname)
    if flags.get('name') is None and flags.get('labels') is None and settings is not None:
        flags['name'] = settings['name']
        flags['labels'] = settings['labels']
        print(f'Using default settings for {hostname} where name: {settings["name"]} and labels: {settings["labels"]}')
        print('If this was not the intention please specify name and labels.')

    error = is_any_none_flags(flags)
    if error is not None:
        raise error

    return flags


def format_flags(flags: dict[str, str]) -> str:
    '''
    Formats the flag dictionary such that it matches the command-line options used for
    config.sh.

    Example Output:
    '--token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX --name runner --labels cuda,opencl,multicore --url https://github.com/diku-dk/futhark'
    
    Returns
    -------
    str
        The formatted string.
    '''

    formatter = lambda pair: f'--{pair[0]} {pair[1]}'
    return ' '.join(map(formatter, flags.items()))
    

def find_process_name(pid: int) -> Optional[str]:
    '''
    Given a pid find the process name. If no process has that pid then None is returned.

    Parameters
    ----------
    pid : int
        The pid that will be used in the search.

    Returns
    -------
    Optional[str]
        The name or None.
    '''
    try:
        name = subprocess.check_output(['ps', '-p', str(pid), '-o', 'comm=']).decode().strip('\n')
    except subprocess.CalledProcessError:
        return None
    
    if name == '':
        return None
    
    return name


def find_child_processes(pid: int) -> list[int]:
    '''
    Given a pid find all the child processes pids that process has.

    Parameters
    ----------
    pid : int
        The process' pid of which the childrens pids will be found.

    Returns
    -------
    Optional[str]
        A list of pids where each pid is a child process.
    '''
    try:
        pids_str = subprocess.check_output(['pgrep', '-P', str(pid)])
    except subprocess.CalledProcessError:
        return []

    return list(map(int, pids_str.split()))


def find_child_search(pid: int, child_name: str) -> Optional[int]:
    '''
    Performs a level-order traversal of the tree of child processes for a given process to find a
    child process with a given name.

    Parameters
    ----------
    pid : int
        The process pid of which the child process will be searched for.
    child_name : str
        The process name that will be searched for.

    Returns
    -------
    Optional[int]
        The pid of the found child process or None if not found.
    '''
    queue = [pid]

    while len(queue) != 0:
        cur_pid = queue.pop(0)
        
        if find_process_name(cur_pid) == child_name:
            return cur_pid
        
        queue.extend(find_child_processes(cur_pid))
    
    return None


def remove_runner(token: str):
    '''
    Tries to remove an old runner from.
    https://github.com/{orginization}/{repository}/settings/actions/runners

    Preconditions
    -------------
        The RUNNER_FOLDER exists.
        A runner is setup in RUNNER_FOLDER.
    '''

    assert(os.path.exists(RUNNER_FOLDER))

    with Chdir(RUNNER_FOLDER):

        name = get_name()
        if os.path.exists('./config.sh'):
            process = subprocess.run(
                ['./config.sh', 'remove', '--token', token],
                env=ENV,
                stdin=subprocess.PIPE
            )
            if process.returncode != 0:
                raise Exception('Error in runner removal: If "Failed: Removing runner from the ' + 
                                'server" try getting the token of the runner from ' + 
                                'https://github.com/SelfHostedRunnerTest/futhark/settings/actions/runners')
    
    shutil.rmtree(RUNNER_FOLDER)
    print(f'The runner named {name} has been removed.')


def stop_runner():
    '''
    Tries to stop the active runner with the pid inside RUNNER_FOLDER/.pid. 

    Preconditions
    -------------
        The RUNNER_FOLDER exists.
        A runner is setup in RUNNER_FOLDER.
    '''

    assert(os.path.exists(RUNNER_FOLDER))
    

    with Chdir(RUNNER_FOLDER):
        
        name = get_name()
        
        if not os.path.exists('.pid'):
            return
        
        pid_str = open('.pid', 'r').read()
        if pid_str == '':
            return
        
        try:
            pid = find_child_search(int(pid_str), 'Runner.Listener')
            if pid is None:
                return
            os.kill(pid, signal.SIGKILL)
            time.sleep(1) # Giving some time for the runner to stop.
            print(f'The runner named {name} has stopped.')
        except ProcessLookupError: pass
    


def clean_up(token: str) -> None:
    '''
    A function that will try to delete and stop the old runner if it exists. If RUNNER_FOLDER/.pid 
    exists and is not empty then the old process is stopped. RUNNER_FOLDER is also removed.

    Incase other runners are running they will not be removed only the runner with a pid inside
    .pid.

    Incase something goes wrong try to remove it manually using:
    'https://github.com/{orginization}/{repository}/settings/actions/runners'
    or end the process manually using the pid found by:
    'pidof Runner.Listener'
    '''

    if not os.path.exists(RUNNER_FOLDER):
        raise Exception(f'{RUNNER_FOLDER} does not exists so the runner can not be cleaned up.')
    
    stop_runner()    
    remove_runner(token)


def start() -> None:
    '''
    Stops an old runner if it is active and starts a new runner.

    Preconditions
    -------------
        The RUNNER_FOLDER exists.
        A runner is setup in RUNNER_FOLDER.
    '''

    stop_runner()

    assert(os.path.exists(RUNNER_FOLDER))

    with Chdir(RUNNER_FOLDER):
        name = get_name()
        
        date = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        p = subprocess.Popen(
            [f'./run.sh > ../log-{date}.txt'],
            env=ENV,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(1) # Letting the process have some time to start up and then search for it's 
                      # childrens pids
        
        with open('.pid', 'w') as fp:
            fp.write(f'{p.pid}')

    print(f'The runner named {name} has started.')


def setup(flags: dict[str, str]) -> None:
    '''
    Setups the runner, a precondition is the RUNNER_FOLDER does not exists.

    Preconditions
    -------------
        The RUNNER_FOLDER does not exist.

    Parameters
    ----------
    flags : dict[str, str]
        The setup flags.
    '''
    install_exception = Exception('Something went wrong doing installation')
    config_exception = Exception(f'''Something went wrong doing configuration.
If the error is: 'A runner exists with the same name'
Then try going to {flags['url'] + '/settings/actions/runners'}
and remove the runner with name: {flags['name']} or use another name.''')

    assert(not os.path.exists(RUNNER_FOLDER))

    os.mkdir(RUNNER_FOLDER)

    with Chdir(RUNNER_FOLDER):
        
        for command in INSTALLATION.split('\n'):
            installation_process = subprocess.run(
                shlex.split(command),
                env=ENV,
                stdin=subprocess.PIPE
            )

            if installation_process.returncode != 0:
                raise install_exception
        
        config_command = shlex.split(f'./config.sh --unattended {format_flags(flags)}')

        print('Running command')
        print(' '.join(config_command))

        config_process = subprocess.run(
            config_command,
            env=ENV,
            stdin=subprocess.PIPE
        )

        if config_process.returncode != 0:
            raise config_exception
        
        name = get_name()
        
        with open('.token', 'w') as fp:
            fp.write(flags['token'])
    
    print(f'The runner named {name} has been setup.')


def main() -> None:
    '''
    The script will try to stop the old runner and remove RUNNER_FOLDER if there is an old runner.
    It will then install the runner using INSTALLATION, setup the runner and then start the runner.
    '''

    flags = get_flags()

    if flags.get('start') is not None and flags.get('start'):
        if os.path.exists(RUNNER_FOLDER):
            start()
        else:
            raise Exception('The runner has to be setup before it can be started.')
        return
    
    if flags.get('kill') is not None and flags.get('kill'):
        if os.path.exists(RUNNER_FOLDER):
            stop_runner()
        else:
            raise Exception('The runner has to be setup before it can be killed.')
        return
    
    if flags.get('remove') is not None:
        clean_up(flags['remove'])
        return

    if os.path.exists(RUNNER_FOLDER) and len(os.listdir(RUNNER_FOLDER)) == 0:
        os.rmdir(RUNNER_FOLDER)
    elif os.path.exists(RUNNER_FOLDER):
        raise Exception('The old runner has to be removed before it can be setup.')

    setup(flags)
    start()


if __name__ == '__main__':
    main()
