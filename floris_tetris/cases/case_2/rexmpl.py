import salabim as sim


class Customer(sim.Component):
    def process(self):
        self.hold(1)
        my_resource.release()


env = sim.Environment()
env.ComponentGenerator(Customer, iat=15)

my_resource = sim.Resource(capacity=1)

env.run()
