import salabim as sim

"""
In this model cars arrive randomly and want to be washed by two washers
The animation shows the queue of waiting card (the requesters of washers) on the left.
for each car, the waiting time is shown as a bar.
On the right are the cars being washed (the claimers of washers), with their total washing time
as an outline and the time spent there.
The animation rectangle object wait_anim of each car, has a dynamic y coordinate and a dynamic size,
which are both implemented as lambda functions that get the car and the time t as parameters.
Note that the fillcolor of wait_animmis changed from red into yellow just by an attribute assignment.
The outline is also a dynamic rectangle with a lambda function for the y position.
"""

ev = 20
spots = 20
evse = 10
fixed = True
sim_time = 50
stay = 10


class CarGenerator(sim.Component):
    def setup(self, ev, spots):
        self.ev = ev
        [
            sim.AnimateRectangle(
                spec=(0, 0, place_w, place_h),
                x=anch_x + (loc // 10) * place_w,
                y=loc % 10 * place_h + anch_y,
                layer=10,
                fillcolor="",
                linecolor="40%gray",
                linewidth=1,
                arg=self,
            )
            for loc in range(0, spots)
        ]

    def process(self):
        car = 0
        while car < self.ev:
            self.hold(sim.Uniform(0, 0)())
            car = EV(kw=sim.Uniform(1, stay - 1)(), stay=stay).sequence_number()


class EV(sim.Component):
    def setup(self, kw, stay):
        self.power_mon = sim.Monitor(
            name="power.", monitor=True, level=True, type="float"
        )
        self.stay = stay
        self.kw = kw
        self.duration_anim = sim.AnimateRectangle(
            spec=(0, padd, self.kw * 10, place_h - 2 * padd),
            x=anch_x + 10 + ((self.sequence_number() - 1) // 10) * place_w,
            y=lambda arg, t: (self.sequence_number() - 1) % 10 * place_h + anch_y,
            text=str(self.name()),
            text_anchor="w",
            text_offsety=2 * padd,
            textcolor="white",
            fillcolor="",
            layer=2,
            linecolor="red",
            linewidth=2,
            arg=self,
            parent=self,
        )
        # self.wait_anim = sim.AnimateRectangle(
        #     spec=lambda arg, t: (
        #         0,
        #         0,
        #         (t - arg.enter_time(list(arg.queues())[0])) * 10,
        #         20,
        #     ),
        #     x=200,
        #     y=lambda arg, t: self.sequence_number() % 10 * 30 + 50,
        #     fillcolor="red",
        #     text=str(self.sequence_number()),
        #     text_anchor="w",
        #     text_offsetx=-20,
        #     textcolor="white",
        #     arg=self,
        #     parent=self,
        # )
        # the lambda function get the car (via arg=self) and t as parameters from the animation engine
        # in this case, the car is exactly in one queue, either washers.requesters() or washers.claimers()
        # therefore list(queues)[0] gives the queue the car is in

    def process(self):
        # if self.sequence_number() == 9:
        #     self.print_info()
        #     print(f"q1{self.queues()}")
        if (fixed == True and self.sequence_number() <= evse) or not fixed:
            self.request(washers)
            # print(f"q2{self.queues()}, time {self.enter_time(list(self.queues())[0])}")
            # if self.sequence_number() == 9:
            #     self.print_info()
            #     print(f"q2{self.queues()}")
            #     print(f"requested kw: {self.kw}")
            duration = self.kw
            # chrg = self.enter_time(list(self.queues())[0]) + duration
            self.duration_anim = sim.AnimateRectangle(
                spec=lambda arg, t: (
                    0,
                    padd,
                    (t - arg.enter_time(list(arg.queues())[0])) * 10,
                    # (((t - arg.enter_time(list(arg.queues())[0]))/1)) * 10,
                    place_h - 2 * padd,
                ),
                layer=1,
                x=anch_x + 10 + ((self.sequence_number() - 1) // 10) * place_w,
                y=lambda arg, t: (self.sequence_number() - 1) % 10 * place_h + anch_y,
                fillcolor="green",
                linecolor="green",
                linewidth=2,
                arg=self,
                parent=self,
            )
            # print(f"q3{self.queues()}, time {self.enter_time(list(self.queues())[0])}")
            # self.duration_anim.fillcolor = "green"
            # self.wait_anim.x = 200
            # if self.sequence_number() == 9:
            #     self.print_info()
            #     print(f"q3{self.queues()}")
            self.power_mon.tally(self.kw)
            self.hold(duration)
            self.power_mon.tally(self.kw)
            # if self.sequence_number() == 9:
            #     self.print_info()
            #     print(f"q4{self.queues()}")
            self.duration_anim.spec = (0, padd, duration * 10, place_h - 2 * padd)
            self.power_mon.tally(0)
            self.hold(self.stay - env.now())
            # self.duration_anim.visible(False)
            # self.print_info()
            # print(f"q4{self.queues()}, time {self.enter_time(list(self.queues())[0])}")
            # self.release(washers)
            # self.hold(self.stay-duration)
        elif fixed == True and self.sequence_number() > evse:
            # self.duration_anim.spec = (0, padd, duration * 10, place_h - 2 * padd)
            self.hold(stay)
            # self.duration_anim.visible(False)


place_w = 100
place_h = 60  # 47
anch_x = 30
anch_y = 70
padd = 13

env = sim.Environment(trace=False)
env.animate(True)
env.modelname("Tetris: the game charger")
env.background_color("20%gray")
sim.AnimateText("Chargers", x=100, y=15, text_anchor="sw")

power_mon = (
    EV("ev.1").power_mon
    + EV("ev.2").power_mon
    + EV("ev.3").power_mon
    + EV("ev.4").power_mon
    + EV("ev.5").power_mon
    + EV("ev.6").power_mon
    + EV("ev.7").power_mon
    + EV("ev.8").power_mon
    + EV("ev.9").power_mon
    + EV("ev.10").power_mon
    + EV("ev.11").power_mon
    + EV("ev.12").power_mon
    + EV("ev.13").power_mon
    + EV("ev.14").power_mon
    + EV("ev.15").power_mon
    + EV("ev.16").power_mon
    + EV("ev.17").power_mon
    + EV("ev.18").power_mon
    + EV("ev.19").power_mon
    + EV("ev.20").power_mon
)
sim.AnimateMonitor(
    power_mon,
    x=500,
    y=10,
    width=500,
    height=300,
    horizontal_scale=10,
    vertical_scale=10,
    nowcolor="blue",
)

washers = sim.Resource(name="washers", capacity=evse)
CarGenerator(ev=ev, spots=spots)

sim.AnimateImage(
    image="floris_tetris/images/parking_wide.png",
    alpha=0,
    x=0,
    y=0,
    width=2000,
    layer=10,
    angle=0,
)

make_video = False
if make_video:
    # env.run(1000)
    # env.animate(do_animate)
    # env.animate3d(do_animate3d)

    # env.video_mode("2d")
    env.video_repeat(0)
    env.show_fps(True)
    # env.show_camera_position()
    env.video("tetris.mp4")
    # env.run(15)
    env.video_mode("2d")
    env.run(sim_time)
    # env.video_mode("screen")
    # env.run(100)

    env.video_close()
else:
    env.run(sim_time)
