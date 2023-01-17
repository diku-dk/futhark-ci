import optparse
import os
from typing import Union


GPUS = {
    'a100',
    'a40',
    'titanrtx',
    'titanx',
    'testlak40',
    'testlak20',
    'gtx1080',
    'gpu'
}


def is_any_none_flags(flags: dict[str, Union[str, None]]) -> Union[Exception, None]:
    '''
    This function checks if any flags are none and reports an error asking for the last arguments
    if sol.
    Parameters
    ----------
    flags : dict[str, Union[str, None]]
        The flags which have been passed to the installation script.
    
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


def format_json_flag(flags: dict[str, None]) -> dict[str, None]:
    flags = flags.copy()
    json = flags['json']
    flags['futhark-options'] = f'--json {json} ' + flags['futhark-options']
    flags['futhark-options'] = flags['futhark-options'].strip()
    return flags


def format_gpu_flag(flags: dict[str, None]) -> dict[str, None]:
    flags = flags.copy()

    if flags.get('gpu') is None:
        flags.pop('gpu')
        return flags
    
    gpu = flags.pop('gpu')
    gpu_args = gpu.split(':')
    if len(gpu_args) > 2:
        raise Exception(f'{gpu} must be given as GPU:AMOUNT or just a GPU name.')
    
    name = ''
    num_of_gpus = ''
    if len(gpu_args) == 1:
        name = gpu_args[0]
        num_of_gpus = '1'
    else:
        name = gpu_args[0]
        num_of_gpus = gpu_args[1]
    
    if name not in GPUS:
        raise Exception(f'{name} is not a valid GPU.')
    elif not num_of_gpus.isnumeric():
        raise Exception(f'{num_of_gpus} is not a valid number of GPUs.')
    
    if name == 'gpu':
        flags['slurm-options'] = f'-p gpu --gres=gpu:{num_of_gpus} ' + flags['slurm-options']
    else:
        flags['slurm-options'] = f'-p gpu --gres=gpu:{name}:{num_of_gpus} ' + flags['slurm-options']
    
    flags['slurm-options'] = flags['slurm-options'].strip()

    return flags


def get_flags() -> dict[str, str]:

    parser = optparse.OptionParser()
    parser.add_option('-g', '--gpu', dest='gpu', type='string', metavar='GPU:AMOUNT',
help='''the name of the GPU to use found here https://diku-dk.github.io/wiki/slurm-cluster
and the specified AMOUNT of gpus formatted as GPU:AMOUNT.''')
    parser.add_option('-f', '--futhark', dest='futhark', type='string', metavar='FUTHARK',
                      help='path to the binaries of the FUTHARK compiler.')
    parser.add_option('-b', '--benchmarks', dest='benchmarks', type='string', metavar='BENCHMARKS',
                      help='path to the BENCHMARKS.')
    parser.add_option('--fo', '--futhark-options', dest='futhark-options', type='string', default='',
                      metavar='FUTHARK-OPTIONS',
                      help='the FUTHARK-OPTIONS that will be passed to the futhark compiler.')
    parser.add_option('-j', '--json', dest='json', type='string', metavar='JSON',
                      help='the path to where the JSON file will go.')
    parser.add_option('--so', '--slurm-options', dest='slurm-options', type='string', default='',
                      metavar='SLURM-OPTIONS',
                      help='the SLURM-OPTIONS that will be passed to slurm.')
    (flags, _) = parser.parse_args()
    flags = flags.__dict__

    flags = format_gpu_flag(flags)
    
    error = is_any_none_flags(flags)
    if error is not None:
        raise error
    
    flags = format_json_flag(flags)
    
    return flags


def main() -> None:
    flags = get_flags()

    futhark = flags['futhark']
    benchmarks = flags['benchmarks']
    futhark_options = flags['futhark-options']
    slurm_options = flags['slurm-options']
    
    with open('temp.sh', mode='w') as fp:
        fp.write('#!/bin/bash\n')
        fp.write(f'{futhark} bench {benchmarks} {futhark_options}')
    
    # for some reason os.chmod does not work.
    os.system('chmod +x temp.sh')
    
    if os.system(f'srun {slurm_options} temp.sh') != 0:
        raise Exception('Something went wrong during srun.')
        
    os.remove('temp.sh')

if __name__ == '__main__':
    main()