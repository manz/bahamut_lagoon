all: rooms.partial
	./build.py

rooms.partial: $(wildcard text/battle/*.xml) $(wildcard text/dialog/*.xml)
	./build.py --rooms

clean:
	rm -f rooms.partial bl.ips
