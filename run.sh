gnome-terminal -- python3 sioManager.py &
gnome-terminal -- python3 sioRepository.py &
sleep 2
max=$1
for i in $(seq 1 $max)
do
        gnome-terminal -- python3 sioClient.py &
done

