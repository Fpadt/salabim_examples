# Car.py
import salabim as sim


class Car(sim.Component):
    def setup(self):
        self.prc = 0
        self.prf = [1,2,3]
        self.dur = None
        self.pwr = None

    def charge(self):
        print(f"time charge1: {env.now()}")        
        self.hold(self.dur)
        print(f"time charge2: {env.now()}")

    def process(self):
        while True:
            print(f"time car process1: {env.now()}\tprc {self.prc}")
            self.passivate()
            li.append(self.dur * self.pwr)
            self.prc += self.dur                
            print(f"time car process2: {env.now()}\tprc {self.prc}")            
            # self.charge()

class TGC_scheduler(sim.Component):
    
    def process(self):
        while True:
            ts = env.now()
            print(ts)
            self.passivate()
            ts = env.now()
            print(ts)                        
            self.hold(1)
            ts = env.now()
            print(ts)                        

class TGC(sim.Component):
    def process(self):
        i=0
        TGCS.activate()
        TGCS.remaining_duration(3)
        print(TGCS.scheduled_time())
        while i < 3:
            EV.dur = EV.prf[i]
            EV.pwr = 5
            print(f"time tgc process1: {env.now()}\tprc {i}")   
            EV.charge()
            print(f"time tgc process1: {env.now()}\tprc {i}") 
            i += 1
            self.standby()  # makes it run every event
            print(f"time tgc process3: {env.now()}\tprc {i}") 

li = []
env = sim.Environment(trace=False)
EV = Car()
TGCS = TGC_scheduler()
TGC()

env.run(till=8)

print(f"Environment end time: {env.now()}")
print(li)
