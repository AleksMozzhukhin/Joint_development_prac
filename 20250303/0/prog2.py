import shlex
import readline

s_1= input("ФИО: ")
s_2 = input('Место: ')

# command='register {} {}'.format(s_1,s_2)
print(tmp:=shlex.join(['register', s_1, s_2]))
print(shlex.split(tmp))