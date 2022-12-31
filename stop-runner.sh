if pidof Runner.Listener > /dev/null; then
	echo "The runner has stopped."
	kill $(pidof Runner.Listener)
else
	echo "There is no runner to stop."
fi