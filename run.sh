# assumes repository root folder is /home/pi/cricket-environmental-control

cd /home/pi/cricket-environmental-control

((count = 10))
while [[ $count -ne 0 ]] ; do
    curl https://github.com > /dev/null
    ping_status=$?
    if [[ $ping_status -eq 0 ]] ; then
        ((count = 1))
    else
        echo "failed pinging github.com. Is there an internet connection?"
        sleep 5
    fi
    ((count = count - 1))
done

if [[ $ping_status -eq 0 ]] ; then
    make update
    make install-requirements
else
    echo "no internet connection. Running without updating."
fi

make run
