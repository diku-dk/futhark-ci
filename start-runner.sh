DATE=$(date '+%Y-%m-%d-%H:%M:%S')
if pidof Runner.Listener > /dev/null; then
	echo "Can not start the runner since a runner is already running."
else
	echo "The runner has started, the log can be found in log-${DATE}.txt."
	nohup ./run.sh &> log-$DATE.txt &
fi