# /// script
# dependencies = [
#   "numpy",
# ]
# ///

print("[Checking] Test 1. Kawa is working")
from kawa import actor, event, NotSupportedEvent, Context, registry
from kawa.cron import CronEvent
print(registry.dump())
print("[Success!] Test 1. Kawa is working")

print("[Checking] Test 2. External dependency is working")
import numpy as np
print(np.zeros((3, 3)))
print("[Success!] Test 2. External dependency is working")
