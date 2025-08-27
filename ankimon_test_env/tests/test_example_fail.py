import sys
import time

print("This test will fail.")
time.sleep(1)
print("Simulating an error condition.")
sys.exit(1)
