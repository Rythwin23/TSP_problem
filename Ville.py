import math


class ville:
    instance = []

    def __init__(self, x, y, id, pop=None, weight=None):
        ville.instance.append(self)
        self.x = x
        self.y = y
        self.id = id
        self.weights = weight
        self.pop = pop

    @classmethod
    def supprimer_toutes_instances(cls):
        for inst in cls.instance:
            del inst

    def getId(self):
        return self.id

    # calcul et retourne la distance entre les deux villes en valeur absolue
    def calcul_Distance(self, city):
        if self.weights is None or (self.pop and not self.pop.choix):
            x = city.x
            y = city.y
            return abs(math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2))

        else:
            return self.weights[city.id]

    def getPosition(self):
        return [self.x, self.y]


# mutation global
"""def mutation(self):
    for _ in range(0, int(len(self.rankPaths) / 100 * self.mutationRate)):
        j = random.randint(0, self.population.getSize() - 1)
        path = self.population.getPaths()[j]
        route = path.getRoute()
        for i in range(0, random.randint(0, 5)):
            index1 = random.randint(0, len(route) - 1)
            index2 = random.randint(0, len(route) - 1)
            route[index1], route[index2] = route[index2], route[index1]
        path.setRoute(route)"""

# héritage paire/impair
'''child = Path()
            genome = [-1] * len(father.getRoute())

            for i in range(0, len(genome)):
                genome[i] = father.getRoute()[i]
                i += 1

            i = 1
            for gene in mother.getRoute():
                if gene not in genome:
                    genome[i] = gene
                    i += 2
            child.setRoute(genome)
            return child'''

#héritage moitié moitié
"""startPos = 0
            endPos = int(len(self.population.cities) / 2)

            route = [None] * len(self.population.cities)

            for i in range(0, len(self.population.cities)):
                if startPos < endPos and startPos < i < endPos:
                    route[i] = father.getCity(i)
                elif startPos > endPos:
                    if not (startPos > i > endPos):
                        route[i] = mother.getCity(i)

            for i in range(0, len(self.population.cities)):
                if mother.getCity(i) not in route:
                    for ii in range(0, len(self.population.cities)):
                        if route[ii] is None:
                            route[ii] = mother.getCity(i)
                            break
            child = Path()
            child.setRoute(route)
            child.mutation(self.mutationRate)
            newborns.append(child)"""
