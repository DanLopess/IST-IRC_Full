import random



with open("cmbt1.info", 'w') as f:
    i = 0
    while i < 50:
        won = random.randint(0,50)
        lost = random.randint(0,50)
        plNr = "".join(["Player", str(i)])

        f.write("#".join([plNr, str(won), str(lost)]) + '\n')
        i += 1