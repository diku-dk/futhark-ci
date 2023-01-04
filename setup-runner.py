import os
import optparse
import datetime
import shutil
import subprocess
import time
import signal
from typing import Union


'''
These are the commands used for installing the self-hosted runner. You may wish to update these
commands with commands from the download box on the website.
https://github.com/{organization}/{repository}/settings/actions/runners/new
'''
INSTALLATION = \
'''curl -o actions-runner-linux-x64-2.299.1.tar.gz -L https://github.com/actions/runner/releases/download/v2.299.1/actions-runner-linux-x64-2.299.1.tar.gz
echo "147c14700c6cb997421b9a239c012197f11ea9854cd901ee88ead6fe73a72c74  actions-runner-linux-x64-2.299.1.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-2.299.1.tar.gz'''


class Chdir:
    '''
    A class for making open with statements for changing working directory instead of the need to
    manange itself.
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
        Goes back to the original working directory when exiting the.
        '''
        os.chdir(self._old_path)


def validate_flags(flags: dict[str, Union[str, None]]) -> None:
    '''
    This function will throw an error if some flags are None.

    Parameters
    ----------
    flags : dict[str, Union[str, None]]
        The flags which have been passed to the installation script.
    
    Raises
    ------
    Exception
        If some of the strings are None.
    '''

    if any(map(lambda opt: opt is None, flags.values())):
        missing_arg_pairs = filter(lambda pair: pair[1] is None, flags.items())
        missing_args = ', '.join(map(lambda pair: pair[0], missing_arg_pairs))
        raise Exception(f'Missing arguments: Please specify {missing_args}.')


def get_flags() -> dict[str, Union[str, None]]:
    '''
    Retrieves the flags given by the user and returns them as a dictionary. The values are either
    strings or None.

    Example Output:
    {
        'token': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        'url': 'https://github.com/diku-dk/futhark',
        'name': 'runner',
        'labels': 'cuda,opencl,multicore'
    }
    
    Returns
    -------
    dict[str, Union[str, None]]
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
    (flags, _) = parser.parse_args()
    flags = flags.__dict__

    if flags.get('url') is None:
        flags['url'] = 'https://github.com/diku-dk/futhark'
    
    validate_flags(flags)

    return flags


def format_flags(flags: dict[str, str]) -> str:
    '''
    Formats the flag dictionary such that it matches the command-line options used for
    configure.sh.

    Example Output:
    '--token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX --name runner --labels cuda,opencl,multicore --url https://github.com/diku-dk/futhark'
    
    Returns
    -------
    str
        The formatted string.
    '''

    formatter = lambda pair: f'--{pair[0]} {pair[1]}'
    return ' '.join(map(formatter, flags.items()))


def str_to_bool(string: str) -> bool:
    '''
    Converts strings to booleans 'y' becomes true and 'n' becomes false.

    Parameters
    ----------
    string : str
        The string that will be converted.

    Raises
    ------
    ValueError
        If the input is not 'y' or 'n'.

    Returns
    -------
    bool
        The converted input.
    '''

    if string == 'y': return True
    elif string == 'n': return False
    raise ValueError("Only 'n' or 'y' can be interpreted as a boolean.")


def user_yes_no_query(question) -> bool:
    '''
    Prints a question which should be a yes or no question and asks for 'n' or 'y' as user input.
    If 'n' or 'y' is not given as input then the user is asked again.

    Parameters
    ----------
    question : str
        The yes or no question asked.

    Returns
    -------
    bool
        If the answer was yes or no. True for 'y' and False for 'n'.
    '''

    print(f'{question} [y/n]', end=' ')
    while True:
        try:
            return str_to_bool(input().lower())
        except ValueError:
            print("Please respond with 'y' or 'n'.")


def clean_up() -> None:
    '''
    A function that will try to delete and stop the old runner if it exists. It removes 
    .actions-runner. If .actions-runner/.pid exists and is not empty then the old process is
    stopped. Also if .actions-runner/.token exists and is not empty then the runner is removed using
    .actions-runner/config.sh.

    Incase other runners not known to .pid and .token then they are not removed.

    Incase something goes wrong try to remove it manually using:
    'https://github.com/{orginization}/{repository}/settings/actions/runners'
    Or end the process manually using the pid found by:
    'pidof Runner.Listener'
    '''

    if not os.path.exists('.actions-runner'):
        raise Exception('.actions-runner does not exists so the runner cannot be cleaned up.')
        
    with Chdir('.actions-runner'):

        if os.path.exists('.token'):
            token = open('.token', 'r').read()
            if token != '':
                os.system(f'./config.sh remove --token {token} > /dev/null')
        
        if os.path.exists('.pid'):
            pid_str = open('.pid', 'r').read()
            if pid_str != '':
                try: os.kill(int(pid_str), signal.SIGKILL)
                except ProcessLookupError: pass
    
    shutil.rmtree('.actions-runner')
    

def find_process_name(pid: int) -> Union[str, None]:
    '''
    Given a pid find the process name. If no process has that pid then None is returned.

    Parameters
    ----------
    pid : int
        The pid that will be used in the search.

    Returns
    -------
    Union[str, None]
        The name or None.
    '''
    name = subprocess.check_output(['ps', '-p', str(pid), '-o', 'comm=']).decode().strip('\n')
    if name == '':
        return None
    return name


def find_child_processes(pid: int) -> list[int]:
    '''
    Given a pid find all the child processes pids that process has.

    Parameters
    ----------
    pid : int
        The process pid of which the child processes pids will be found.

    Returns
    -------
    Union[str, None]
        A list of pids where each pid is a child process.
    '''
    try:
        pids_str = subprocess.check_output(['pgrep', '-P', str(pid)])
    except subprocess.CalledProcessError:
        return []

    return list(map(int, pids_str.split()))


def find_child_search(pid: int, child_name: str) -> Union[int, None]:
    '''
    Performs a level-order traversal of the tree of child process for a given process to find the
    child process with a given name.

    Parameters
    ----------
    pid : int
        The process pid of which the child process will be searched for.
    child_name : str
        The process name that will be searched for.

    Returns
    -------
    Union[int, None]
        The pid of the found child process or None if not found.
    '''
    queue = [pid]

    while len(queue) != 0:
        cur_pid = queue.pop(0)
        
        if find_process_name(cur_pid) == child_name:
            return cur_pid
        
        queue.extend(find_child_processes(cur_pid))
    
    return None


def main() -> None:
    '''
    The script will try to stop the old runner and remove .actions-runner if there is an old runner.
    It will then install the runner using INSTALLATION, setup the runner and then start the runner.
    '''

    if os.path.exists('.actions-runner'):
        if not user_yes_no_query('Is it okay to delete the old runner?'):
            return

    clean_up()
    
    flags = get_flags()

    install_exception = Exception('Something went wrong doing installation')
    config_exception = Exception(f'''Something went wrong doing configuration.
If the error is: 'A runner exists with the same name'
Then try going to to {flags['url'] + '/settings/actions/runners'}
and remove the runner with name: {flags['name']}''')

    os.mkdir('.actions-runner')
    
    with Chdir('.actions-runner'):
        if os.system(INSTALLATION.replace('\n', r'&&')) != 0:
            raise install_exception
        if os.system(f'./config.sh --unattended {format_flags(flags)}') != 0:
            raise config_exception
    
        date = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        command = [f'./run.sh > ../log-{date}.txt']
        p = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(1) # Letting the process have some time to start up and then search for it's 
                      # childrens pids
        pid = find_child_search(p.pid, 'Runner.Listener')
        
        if pid is not None:
            with open('.pid', 'w') as fp:
                fp.write(f'{pid}')
        
        with open('.token', 'w') as fp:
            fp.write(flags['token'])


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    main()