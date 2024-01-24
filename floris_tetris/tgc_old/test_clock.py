# Car.py
import salabim as sim


class TGC_clock(sim.Component):
    
    def process(self):
        while True:
            self.passivate()
            

class TGC(sim.Component):
    def setup(self):
        self._clock = TGC_clock()

    def process(self):
        while True:
            ts = env.now()
            print(ts) 
            self._clock.activate()
            self._clock.remaining_duration(3)
            # print(self._clock.scheduled_time())        
            # ts = env.now()
            # print(ts)      
            self.standby()  # makes it run every event
            # ts = env.now()
            # print(ts)  


env = sim.Environment(trace=False)
# TGCC = TGC_clock()
TGC()

env.run(till=8)


