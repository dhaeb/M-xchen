from rx import Observable, Observer
import random
import time
from threading import current_thread

from rx import Observable
from rx.concurrency import NewThreadScheduler

def push_five_strings(observer):
        observer.on_next("Alpha")
        observer.on_next("Beta")
        observer.on_next("Gamma")
        observer.on_next("Delta")
        observer.on_next("Epsilon")
        observer.on_completed()

def intense_calculation(value):
    # sleep for a random short duration between 0.5 to 2.0 seconds to simulate a long-running calculation
    time.sleep(random.randint(5, 20) * .1)
    return value


# calculate number of CPU's, then create a ThreadPoolScheduler with that number of threads
pool_scheduler = NewThreadScheduler()

def p(e):
    print(e)

# Create Process 1
o = Observable.from_(["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]) \
    .map(lambda s: intense_calculation(s)) \
    .subscribe_on(pool_scheduler)# \
#    .subscribe(on_next=p,
#               on_error=p,
#               on_completed=lambda: p("PROCESS 1 done!"))
#
# Create Process 2s

class PrintObserver(Observer):

    def on_next(self, value):
        print(current_thread().getName())
        print("Received {0}".format(value))

    def on_completed(self):
        print("Done!")

    def on_error(self, error):
        print("Error Occurred: {0}".format(error))

source = Observable.create(push_five_strings)

p = source.map(lambda s: intense_calculation(s)) \
      .subscribe_on(pool_scheduler)

Observable.merge(o,p).subscribe(PrintObserver())
print(type(p))


input("Press any key to exit\n")
