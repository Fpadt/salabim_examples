import salabim as sim
import numpy as np
import matplotlib.pyplot as plt

class TGC0(sim.Component):

    def setup(self):
        pass

    def process(self):
        self.passivate()
        ts = env.now()        
        self.hold(10, priority=0)
        ts = env.now()
        i_EV.pwr = 3
        i_EV.remaining_duration(10)
                  
    def request_power(self, power, duration):
        return {"power": power, "duration": duration}

class EV0(sim.Component):
    def setup(self):
        self._mon = sim.Monitor("pwr", level=True, initial_tally=0)
        self._pwr = 0

    @property
    def pwr(self):
        return self._pwr
    
    @pwr.setter
    def pwr(self, value):
        self._pwr = value
        self._mon.tally(self._pwr)


    def process(self):
        k = 0
        
        while k < 1:        
            i = 1
            ts = env.now()            
            self.hold(5) # wait till ev arrives
            ts = env.now()            
            # arrives and requests power
            response = iTGC.request_power(7, 15)
            self._pwr = response["power"]
            iTGC.activate()

            while i < 2:
                self._mon.tally(self._pwr)
                ts = env.now()                
                self.hold(response["duration"], priority=1)
                ts = env.now()
                i += 1
            self.pwr = 0
            k += 1

        self.hold(10)
        self.pwr = 0
        
        df = self._mon.as_dataframe()
        plt.step(df['t'], df['pwr.x'], where='post')

        plt.xlabel('t')
        plt.ylabel('cap')
        plt.title('Step Plot')

        plt.show()

class TGC(sim.Component):

    def setup(self):
        pass

    def process(self):
        self.passivate()
                  
    def request_power(self, power, duration):
        return {"power": power, "duration": duration}

class EV(sim.Component):
    def setup(self):
        self._mon = sim.Monitor("pwr", level=True, initial_tally=0)
        self._pwr = 0

    @property
    def pwr(self):
        return self._pwr
    
    @pwr.setter
    def pwr(self, value):
        self._pwr = value
        self._mon.tally(self._pwr)

    @property
    def e_c(self):
        df = self._mon.as_dataframe()
        eic = (
            df.assign(
                t2=df["t"].shift(-1),
                dt=lambda df: df["t2"] - df["t"],
                cp=lambda df: df["dt"] * df["pwr.x"],
            )["cp"]
            .sum(skipna=True)
         )
        return eic


    def process(self):
        k = 0
        self.hold(5) # wait till ev arrives        
        
        # mimic 80%
        while self.e_c < 0.8 * 70:        
            i = 1
            # arrives and requests power
            response = iTGC.request_power(7, 4)
            self._pwr = response["power"]
            while i < 2:
                self._mon.tally(self._pwr)       
                self.hold(response["duration"], priority=1)
                i += 1
            self.pwr = 0
            k += 1

        while self.e_c < 0.9 * 70:      
            i = 1
            response = iTGC.request_power(5, 5)
            self._pwr = response["power"]

            while i < 2:
                self._mon.tally(self._pwr)       
                self.hold(response["duration"], priority=1)
                i += 1
            self.pwr = 0
            k += 1

        self.hold(10)
        self.pwr = 0
        
        df = self._mon.as_dataframe()
        plt.step(df['t'], df['pwr.x'], where='post')

        plt.xlabel('t')
        plt.ylabel('cap')
        plt.title('Step Plot')

        plt.show()



env = sim.Environment(trace=False)

iTGC = TGC()
i_EV = EV()

env.run()        