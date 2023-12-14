# Bank, 3 clerks (with ComponentGenerator).py
import salabim as sim


class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
                break  # activate at most one clerk
        self.passivate()


class Clerk(sim.Component):
    def setup(self):
        if EVSE.available_quantity() > 0:
            self.request(EVSE)
            self.evse = True
        else:
            self.evse = False

    def process(self):
        while True:
            while len(waitingline) == 0:
                self.passivate()
            self.customer = waitingline.pop()
            if self.charger:
                self.hold(20)
                self.charged = True
            else:
                self.hold(30)
                self.charged = False
            self.customer.activate()
            print(
                f"Cl: {self.name()} CH: {self.charger} EV: {self.customer.name()} CHRGD: {self.charged} AT: {env.now()}"
            )


env = sim.Environment(trace=False)

env.ComponentGenerator(Customer, iat=15, number=4, force_at=True)

EVSE = sim.Resource("EVSE", capacity=1)

clerks = [Clerk() for _ in range(2)]

waitingline = env.Queue("waitingline")

env.run(till=600)

# waitingline.print_histograms()
# waitingline.print_info()
