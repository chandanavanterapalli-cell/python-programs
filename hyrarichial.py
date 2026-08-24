class parent:
    def show(self):
        print("parent method")
class child1(parent):
    pass
class child2(parent):
    pass

c=child1()
c.show()
c1=child2()        
c.show()