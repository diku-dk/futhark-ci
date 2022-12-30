# Setting up Self-hosed Runners
This guide assumes Linux is use, but it will probably be much the same for different operating systems and similar guides can be found the links referenced in the guide.
## Installation
Go to the Futhark repository then navigate from Settings $\to$ Actions $\to$ Runners and then click the [New self-hosted runner](https://github.com/SelfHostedRunnerTest/futhark/settings/actions/runners/new) button.

Now execute every command in the `Download` box on the machine where the self-hosted runner will be setup. The name of the folder may be changed to something else instead of `actions-runner` if needed.
## Configuration
To configure the self-hosted runner first navigate to self-hosted runner (assuming you are not already there). Now find the command in the `configure` box which looks like this.
```
./config.sh --url https://github.com/diku-dk/futhark --token XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
If it is possible to set it up then it should respond with `√ Connected to GitHub`. After this some different parameters can be set. The name of the runner group, the name of the runner and the name of the work folder may be changed or left as default.

The **important parameter** is which labels the self-hosted runner should have.

```
Enter any additional labels (ex. label-1,label-2): [press Enter to skip]
```
One to three of the following labels should be given to indicate which benchmarks can be executed on the machine `CUDA`, `OpenCL` or `Multicore`. An example could be if you wanted to setup a self-hosted runner which is able to run all three benchmark then type in the following and press enter.
```
CUDA,OpenCL,Multicore
```
In case the self-hosted runner is not correctly configured `./config.sh` can be executed again with all its parameters and a new token. This will initiate the reconfiguration of the self-hosted runner.
## Deployment
Inside the folder of self-hosted runner can a shell script be found that will run the self-hosted runner. This script can be executed using `./run.sh` but before executing it make sure the correct [environment variables](https://github.com/diku-dk/howto/blob/main/servers.md#environment-variables) are set which will allow the use of the GPUs. `run.sh` could be used to test if the self-hosted runner runs the benchmarks as expected. In the long term it should be setup as a service. To do this put the shell script [svc-install.sh](svc-install.sh) inside the self-hosted runner folder and execute it.
```
chmod +x svc-install.sh && sudo ./svc-install.sh
```
This script will perform `sudo ./svc.sh install` and set up environment variables for the GPUs for that service. Then to start the service do.
```
sudo ./svc.sh start
```
To stop it do `sudo ./svc.sh stop`, to uninstall it do `sudo ./svc.sh uninstall` and to check the status of the service do `sudo ./svc.sh status`. For further reading about this look at the [Configuring the self-hosted runner application as a service](https://docs.github.com/en/actions/hosting-your-own-runners/configuring-the-self-hosted-runner-application-as-a-service?platform=linux) article.


