all: rooms.partial assets/vwf.bin
	./build.py

rooms.partial: $(wildcard text/battle/*.xml) $(wildcard text/dialog/*.xml)
	./build.py --rooms

assets/vwf.bin: $(wildcard fonts/vwf*.png)
	mkdir -p assets 
	python ./utils/font.py

clean:
	rm -f rooms.partial bl.ips
	rm -f assets/vwf.bin
