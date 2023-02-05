#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 9), "Use Python 3.9 or newer."

import optparse
import os
import stat
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

    for flag in mapping.copy().keys():
        if flags.get(flag) is None:
            flags.pop(flag)
            continue
        
        value = flags.pop(flag)
        if isinstance(value, bool):
            if value:
                flags[collapsed] += f' {mapping[flag]}'
        else:
            flags[collapsed] += f' {mapping[flag]}={value}'

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
        'tests': '/path/to/tests/',
        'futhark-options': --some --valid --futhark --options,
        'slurm-options': --some --valid --slurm --options
    }
    
    Returns
    -------
    dict[str, str]
        The new formatted flags.
    '''

    parser = optparse.OptionParser()
    parser.add_option('--gres', dest='gres', type='string', metavar='GRES',
                      help=('The flags corresponding to GRES found here '
                            'https://slurm.schedmd.com/srun.html '))
    parser.add_option('--futhark', dest='futhark', type='string', metavar='FILE',
                      help='Path to tar FILE with the binaries of the futhark.')
    parser.add_option('--tests', dest='tests', type='string', metavar='PATH',
                      help='PATH to the tests.')
    parser.add_option('--futhark-options', dest='futhark-options', type='string', default='',
                      metavar='FUTHARK-OPTIONS',
                      help='The options that will be passed to the futhark compiler.')
    parser.add_option('--slurm-options', dest='slurm-options', type='string', default='',
                      metavar='SLURM-OPTIONS',
                      help='The options that will be passed to slurm.')
    parser.add_option('--backend', dest='backend', type='string', metavar='BACKEND',
                      help=('The BACKEND used when compiling Futhark programs (without leading '
                            'futhark, e.g. just opencl).'))
    parser.add_option('--partition', dest='partition', type='string', metavar='NAME',
                      help='Request a specific partition for the resource allocation.')
    parser.add_option('--job-name', dest='job-name', type='string', metavar='NAME',
                      help='Specify a NAME for the job.')
    parser.add_option('--exclude', dest='exclude', type='string', metavar='tag',
                      help=('Do not run test cases that contain the given tag. Cases marked with '
                            '“nobench”, “disable”, or “no_foo” (where foo is the backend used) are '
                            'ignored by default..'))
    parser.add_option('--cache-extension', dest='cache-extension', type='string', metavar='NAME',
                      help=('For a program foo.fut, pass --cache-file foo.fut.EXTENSION. By '
                            'default, --cache-file is not passed.'))
    parser.add_option('-c', dest='c', action='store_true',
                      help=('Only run compiled code - do not run the interpreter. '
                            'This is the default.'))
    parser.add_option('-C', dest='C', action='store_true',
                      help='Test with the interpreter.')
    parser.add_option('-i', dest='i', action='store_true',
                      help='Compile the programs, but do not run them.')
    parser.add_option('-t', dest='t', action='store_true',
                      help='Type-check the programs, but do not run them.')
    parser.add_option('--no-terminal', dest='no-terminal', action='store_true',
                      help='Print each result on a line by itself, without line buffering.')
    parser.add_option('--no-tuning', dest='no-tuning', action='store_true',
                      help='Do not look for tuning files.')
    parser.add_option('--concurrency', dest='concurrency', metavar='NUM',
                      help=('The number of tests to run concurrently. Defaults to the number of ' 
                            '(hyper-)cores available.'))
    parser.add_option('--pass-option', dest='pass-option', metavar='opt',
                      help='Pass an option to benchmark programs that are being run.')
    parser.add_option('--pass-compiler-option', dest='pass-compiler-option', metavar='opt',
                      help='Pass an extra option to the compiler when compiling the programs.')
    parser.add_option('--runner', dest='runner', metavar='program',
                      help=('If set to a non-empty string, compiled programs are not run directly, ' 
                            'but instead the indicated program is run with its first argument ' 
                            'being the path to the compiled Futhark program. This is useful for '
                            'compilation targets that cannot be executed directly (as with '
                            'futhark-pyopencl on some platforms), or when you wish to run the '
                            'program on a remote machine.'))
    parser.add_option('--tuning', dest='tuning', metavar='EXTENSION',
                      help=('For each program being run, look for a tuning file with this '
                            'extension, which is suffixed to the name of the program. For example, '
                            'given --tuning=tuning (the default), the program foo.fut will be '
                            'passed the tuning file foo.fut.tuning if it exists.'))
    parser.add_option('--cpus-per-task', dest='cpus-per-task', type='string', metavar='ncpus',
                      help='Request that ncpus be allocated per process.')
    parser.add_option('--mem', dest='mem', metavar='sizee[units]',
                      help='Specify the real memory required per node. Default units are megabytes.')
    (flags, _) = parser.parse_args()
    flags = flags.__dict__
    
    futhark_options_mapping = {
        'backend': '--backend',
        'exclude': '--exclude',
        'cache-extension': '--cache-extension',
        'c': '-c',
        'C': '-C',
        'concurrency': '--concurrency',
        'i': '-i',
        't': '-t',
        'no-terminal': '--no-terminal',
        'no-tuning': '--no-tuning',
        'pass-option': '--pass-option',
        'pass-compiler-option': '--pass-compiler-option',
        'runner': '--runner',
        'tuning': '--tuning',
    }

    slurm_options_mapping = {
        'gres': '--gres',
        'partition': '--partition',
        'job-name': '--job-name',
        'cpus-per-task': '--cpus-per-task',
        'mem': '--mem'
    }

    flags = collapse_flags(flags, slurm_options_mapping, 'slurm-options')
    flags = collapse_flags(flags, futhark_options_mapping, 'futhark-options')

    error = is_any_none_flags(flags)
    if error is not None:
        raise error
    
    return flags


def main() -> None:
    flags = get_flags()

    futhark = flags['futhark']
    tests = flags['tests']
    futhark_options = flags['futhark-options']
    slurm_options = flags['slurm-options']

    script = 'temp.sh'
    with open(script, mode='w') as fp:
        fp.write('#!/bin/bash\n')
        fp.write(f'{futhark} test {tests} {futhark_options}')
    
    os.chmod(script, os.stat(script).st_mode | stat.S_IEXEC)
    
    print('Running Tests:')
    if os.system(f'srun {slurm_options} temp.sh') != 0:
        raise Exception('Something went wrong during srun.')
        
    os.remove(script)


if __name__ == '__main__':
    main()