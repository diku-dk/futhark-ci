#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 9), "Use Python 3.9 or newer."

import optparse
import os
import stat
import pprint
from typing import Optional


def is_any_none_flags(flags: dict[str, Optional[str]]) -> Optional[Exception]:
    '''
    This function checks if any flags are none and reports an error asking for the last arguments
    if sol.
    Parameters
    ----------
    flags : dict[str, Union[str, None]]
        The flags which have been passed to the script.
    
    Returns
    -------
    bool
        True if the flags were valid otherwise false.
    Union[Exception, None]
        None if the flags were valid otherwise a corresponding error.
    '''
    if any(map(lambda opt: opt is None, flags.values())):
        missing_arg_pairs = filter(lambda pair: pair[1] is None, flags.items())
        missing_args = ', '.join(map(lambda pair: pair[0], missing_arg_pairs))
        return Exception(f'Missing arguments: Please specify {missing_args}.')

    return None


def collapse_flags(flags: dict[str, Optional[str]],
                   mapping: dict[str, str],
                   collapsed: str) -> dict[str, Optional[str]]:
    flags = flags.copy()

    for flag in flags.copy().keys():
        if flags.get(flag) is None or mapping.get(flag) is None:
            continue
        
        flags[collapsed] += f' --{mapping[flag]}={flags.pop(flag)}'

    flags[collapsed] = flags[collapsed].strip()

    return flags


def get_flags() -> dict[str, str]:
    '''
    Retrives the flags passed to the script and checks them for their validity and returns them.
    The flags return should be a dictionary with only four keys. Do not set --gres or -p manually
    for slurm and dot not set --json manually for futhark.

    Example:
    {
        'futhark': '/path/to/futhark.tar.xv',
        'benchmarks': '/path/to/benchmarks/',
        'futhark-options': --some --valid --futhark --options,
        'slurm-options': --some --valid --slurm --options
    }
    
    Returns
    -------
    dict[str, str]
        The new formatted flags.
    '''

    parser = optparse.OptionParser()
    parser.add_option('--gres', dest='gres', type='string', metavar='GRES', default='',
                      help=('The flags corresponding to GRES found here '
                            'https://slurm.schedmd.com/srun.html '))
    parser.add_option('--futhark', dest='futhark', type='string', metavar='FILE',
                      help='Path to tar FILE with the binaries of the futhark.')
    parser.add_option('--benchmarks', dest='benchmarks', type='string', metavar='PATH',
                      help='PATH to the benchmarks.')
    parser.add_option('--futhark-options', dest='futhark-options', type='string', default='',
                      metavar='FUTHARK-OPTIONS',
                      help='The options that will be passed to the futhark compiler.')
    parser.add_option('--json', dest='json', type='string', metavar='FILE', 
                      help='The path to where the json FILE will go.')
    parser.add_option('--slurm-options', dest='slurm-options', type='string', default='',
                      metavar='SLURM-OPTIONS',
                      help='The options that will be passed to slurm.')
    parser.add_option('--exclude', dest='exclude', type='string', metavar='EXCLUDE', default='',
                      help=('Do not run test cases that contain the given tag. Cases marked with '
                            '“nobench”, “disable”, or “no_foo” (where foo is the backend used) are '
                            'ignored by default..'))
    parser.add_option('--backend', dest='backend', type='string', metavar='BACKEND',
                      help=('The BACKEND used when compiling Futhark programs (without leading '
                            'futhark, e.g. just opencl).'))
    parser.add_option('--ignore-files', dest='ignore-files', type='string', metavar='PATH', default='',
                      help='Ignore files whose PATH match the given regular expression.')
    parser.add_option('--partition', dest='partition', type='string', metavar='NAME', default='',
                      help='Request a specific partition for the resource allocation.')
                      
    (flags, _) = parser.parse_args()
    flags = flags.__dict__
    
    futhark_options_mapping = {
        'backend': 'backend',
        'ignore-files': 'ignore-files',
        'exclude': 'exclude',
        'json': 'json'
    }

    slurm_options_mapping = {
        'gres': 'gres',
        'parition': 'partition'
    }
     
    flags = collapse_flags(flags, slurm_options_mapping, 'slurm-options')
    flags = collapse_flags(flags, futhark_options_mapping, 'futhark-options')

    pprint.pprint(flags)

    error = is_any_none_flags(flags)
    if error is not None:
        raise error
    
    return flags


def main() -> None:
    flags = get_flags()

    futhark = flags['futhark']
    benchmarks = flags['benchmarks']
    futhark_options = flags['futhark-options']
    slurm_options = flags['slurm-options']

    cwd = os.getcwd()

    get_data_script = "get-data.sh"
    os.chdir(benchmarks)
    if not os.path.exists(get_data_script):
        raise Exception(f'The script "{get_data_script}" does not exist.')

    print('Getting Benchmark Data:')
    get_data_command = f'./{get_data_script} external-data.txt'
    if os.system(get_data_command) != 0:
        raise Exception(f'Something went wrong during "{get_data_command}".')
    os.chdir(cwd)

    script = 'temp.sh'
    with open(script, mode='w') as fp:
        fp.write('#!/bin/bash\n')
        fp.write(f'{futhark} bench {benchmarks} {futhark_options}')
    
    os.chmod(script, os.stat(script).st_mode | stat.S_IEXEC)
    
    print('Running Benchmark:')
    if os.system(f'srun {slurm_options} temp.sh') != 0:
        raise Exception('Something went wrong during srun.')
        
    os.remove(script)


if __name__ == '__main__':
    main()