class Grandparent:
    def property(self):
        print("Grand parentbproperty")
class Parent(Grandparent):
    pass
class Child(Parent):
    pass
c=Child()      
c.property()  