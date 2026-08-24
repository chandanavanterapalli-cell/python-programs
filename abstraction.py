from abc import ABC,  abstractmethod
class vechicle:
    def start(self):
        pass
class car(vechicle):
    def start(self):
        print("car started")
c=car() 
c.start()      