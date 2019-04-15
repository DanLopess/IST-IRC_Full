import random



with open("logs1.info", 'w') as f:
    i = 0
    while i < 50:
        dst = random.randint(0,50)
        food = random.randint(0,100)
        traps = random.randint(0, 10)
        train = random.randint(0, 60)
        plNr = "".join(["Player", str(i)])

        f.write("#".join([plNr, str(dst), str(food), str(traps), str(train)]) + '\n')
        i += 1
        