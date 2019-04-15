import random

with open("stats1.info", 'w') as f:
    i = 0
    while i < 50:
        atk = random.randint(0,50)
        defs = 50 - atk
        enr = random.randint(5, 100)
        exp = random.randint(0, 500)
        combt = random.randint(0,100)
        plNr = "".join(["Player", str(i)])

        f.write("#".join([plNr, str(atk), str(defs), str(enr), str(exp), str(combt)]) + '\n')
        i += 1

