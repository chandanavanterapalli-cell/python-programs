class father:
    def skill(self):
        print("driving")
class mother:
    def skill2(self):
        print("cooking")     
class child(father,mother):
    pass         
c=child()
c.skill()
c.skill2()