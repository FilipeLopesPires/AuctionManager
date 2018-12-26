xterm -hold -e "python3 sioManager.py" &
xterm -hold -e "python3 sioRepository.py" &
sleep 1
xterm -hold -e "python3 sioClient.py" &
