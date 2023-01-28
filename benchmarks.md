# Running Benchmarks
## Setup
Copy the [actions](benchmark-workflow/actions/) folder to the `.github` folder of the futhark repository.

## `slurmbench.py` and Github Action
The intended use of slurmbench.py is by using the existing [composite action](benchmark-workflow/actions/benchmark). An example of this can be seen below and found [here](benchmark-workflow/workflows/main.yml).
```yml
benchmark-titanrtx-opencl:
  runs-on: [titanrtx, opencl]
  needs: [build-linux-nix]
  if: github.repository == 'diku-dk/futhark' && !github.event.pull_request.draft
  steps:
  - uses: actions/checkout@v3
    with:
    submodules: recursive
    fetch-depth: 0
  - uses: ./.github/actions/benchmark
    with:
    backend: opencl
    system: titanrtx
    gpu: titanrtx:1
```
The job will use any runner which have both of the labels `titanrtx` and `opencl`. If it is the case that Slurm is installed then `srun` will be used else the benchmarks will be executed on the system without Slurm. The arguments that can be specified are.
* `gpu:` is the GPU and amount of that GPUs to use. You may just write `gpu: GPU` then it will default to one GPU. If `gpu: none` is specified, or it is not specified then no GPU will be used for Slurm. It is important that the GPU match the name of some available GPU on the cluster using slurm.
* `backend:` specifies the backend to be used for the Futhark compiler, this could be `cuda`, `opencl` or `multicore`.
* `system: ` name of the system.
* `options: ` extra options to parse to the Futhark compiler.
* `slurm: ` extra options to parse to `srun`.

## `slurmbench.py`
The way `slurmbench.py` is best understood looking at the [code](slurmbench.py). An example use case of `slurmbench.py` is.
```bash
python3.9 slurmbench.py \
    --gpu=gpu \
    --futhark=path/to/futhark/compiler \
    --slurm-options='--some --slurm --flags' \
    --futhark-options='--some --futhark --flags' \
    --json=path/to/result.json \
    --benchmarks=path/to/futhark-benchmarks
```
This script will start a Slurm job using `srun` with the specified flags running the benchmarks in the `path/to/futhark-benchmarks` folder. The `gpu` flag must be a valid GPU and amount of GPUs. The benchmarks will be run using the binaries `path/to/futhark/compiler` with the specified flags. The `json` flag will be the path where the benchmark results will be put.

## Collection of results
Inside the [benchmark example](benchmark-workflow/workflows/main.yml) there is a job `benchmark-results` that will collect the results. If anyone or more of the benchmarks fail this job will run and try to upload the results due to `${{ always() }}`.
