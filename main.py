import operator
import random
import time
import tkinter as tk
import matplotlib.pyplot as plt
import networkx as nx
from Ville import ville


class Path:
    instance = []

    def __init__(self):
        Path.instance.append(self)
        self.route = []
        self.distance = 0
        self.fitness = 0.0

    # une classmethod qui permettra de liberer la mémoire en supprimant les paths
    @classmethod
    def supprimer_toutes_instances(cls):
        for inst in cls.instance:
            del inst

    # renvoie la distance du trajet du path, si celle ci est null il la calcule avant
    def getDistance(self):
        if self.distance == 0:
            for i in range(0, len(self.route) - 1):
                self.distance += self.route[i].calcul_Distance(self.route[i + 1])
            self.distance += self.route[0].calcul_Distance(self.route[-1])
            return self.distance
        else:
            return self.distance

    # renvoie la fitness du path, si celle ci est null il la calcule avant
    def getFitness(self):
        if self.fitness == 0:
            self.fitness = 1 / float(self.getDistance())
            return self.fitness
        else:
            return self.fitness

    # renvoie le trajet du path, en forme de liste d'objets de ville
    def getRoute(self):
        return self.route

    # renvoie le trajet du path en liste, mais avec uniquement l'id des villes
    def getRouteId(self):
        result = []
        for v in self.route:
            result.append(v.getId())
        return result

    # renvoie la ville qui se trouve à la position i du trajet du path
    def getCity(self, position):
        return self.route[position]

    # fonction appelé pour donner un chemin spécifique au path
    # si le chemin donné est null elle utilise la liste des villes pour se créer un chemin aléatoire
    def setRoute(self, route=None, listCities=None):
        if route is None:
            random.shuffle(listCities)
            self.route = listCities
        else:
            self.route = route

        # reinitialise les caractéristiques pour qu'ils soient calculé après
        self.distance = 0
        self.fitness = 0

    # fonction pour faire muter un path (mutation de génome à la naissance)
    # pour muter, elle inverse la position de deux villes prise au hasard dans le trajet
    # le pourcentage de mutation "m"% indique qu'il y aura au plus "m"% mutation dans le genome
    def mutation(self, m):
        for i in range(0, int(len(self.route) / 100 * m)):
            index1 = random.randint(0, len(self.route) - 1)
            index2 = random.randint(0, len(self.route) - 1)
            self.route[index1], self.route[index2] = self.route[index2], self.route[index1]


class Population:
    instance = []

    def __init__(self, cities, nbcities):
        Population.instance.append(self)
        self.paths = []
        self.cities = cities
        self.nbcities = nbcities
        self.choix = False
        if self.cities is None:
            self.cities = self.generate_cities()
            # si le programme démarre sans une liste de ville prédéfinie elle génère elle-même ses villes,
            # en respectant le nombre de villes à créer

    # une classmethod qui permettra de liberer la mémoire en supprimant l'objet population
    @classmethod
    def supprimer_toutes_instances(cls):
        for inst in cls.instance:
            del inst

    # génére les villes aléatoire
    def generate_cities(self):
        cities = []
        print("Génération des villes et des poids des chemins :")
        for i in range(0, self.nbcities):
            x = random.randint(0, 250)
            y = random.randint(0, 250)
            cities.append(ville(x, y, i, self))

        # les poids sont utilisé au cas où on veuille autre chose que la distance comme poids des arêtes
        # Générez des poids aléatoires pour chaque paire de villes
        weights = {}
        for i in range(self.nbcities):
            # Initialisez une liste vide pour stocker les poids de cette ville vers d'autres villes
            weights[i] = []
            for other_city in cities:
                if other_city.getId() != i:
                    weight = random.randint(10, 200)  # Générez un poids aléatoire entre 1 et 100
                    weights[i].append(weight)  # Ajoutez le poids à la liste correspondante dans le dictionnaire
                else:
                    weights[i].append(0)

        # unifier les poids entre deux villes pour l'aller et le retour (une même arête aura le meme
        #                                                               poids dans les deux sens)
        for cle, valeur in weights.items():
            for i in range(len(valeur)):
                if i != cle:
                    valeur[i] = weights[i][cle]

        # associer à chaque ville le poids vers les autres villes
        for city in cities:
            city.weights = weights[city.getId()]
            print(f'Ville: {city.getId()}, pos: ({city.x},{city.y}), poids: {city.weights}')

        return cities

    def initialPopulation(self, nb):
        self.paths = []
        for i in range(0, nb):
            random.shuffle(self.cities)
            p = Path()
            p.setRoute(None, self.cities)
            self.paths.append(p)

    # récupère tous les paths de la population
    def getPaths(self):
        return self.paths

    # ajoute un nouvel individu 'path'
    def addPath(self, p):
        self.paths.append(p)

    # supprimer un individu existant 'path'
    def removePath(self, p):
        self.paths.remove(p)

    # récupère la taille de la population
    def getSize(self):
        return len(self.paths)

    # renvoie la distance moyenne parcourue par les paths (faire la moyenne de toutes leurs distances)
    def getAverageDistance(self):
        d = []
        for p in self.paths:
            d.append(p.getDistance())
        return sum(d) / len(d)


class GeneticAlgorith:
    instance = []

    def __init__(self, pop, gen, repeat, nb, bornrate, deathrate, mutationrate):
        GeneticAlgorith.instance.append(self)
        self.population = pop
        self.nbIndividu = nb
        self.repeat = repeat
        self.finalGeneration = gen
        self.generation = 0
        self.rankPaths = None
        self.bestPath = None
        self.run = True
        self.figure = None
        self.choix = False
        self.graph = nx.DiGraph()
        self.bornRate = bornrate
        self.deathRate = deathrate
        self.mutationRate = mutationrate

    @classmethod
    def supprimer_toutes_instances(cls):
        for inst in cls.instance:
            del inst

    # méthode pour controler le début de l'algo génétique,
    # on prépare et active le mode intéractif de la figure plt pour un affichage dynamique avec plt.ion()
    def start(self):
        final = None
        plt.ion()

        # faire x simulation avec la meme population et les memes villes (x = self.repeat)
        # cela va marcher tant que le programme n'est pas arrêté aka self.run = False
        for i in range(1, self.repeat + 1):
            Path.supprimer_toutes_instances()
            if self.run is False:
                break
            else:
                self.population.choix = self.choix  # est utilisé pour faire un choix entre utiliser la distance ou le poids pour les paths
                self.population.initialPopulation(self.nbIndividu)  # initialise la premiére génération d'individus
                self.generation = 0
                self.evolution()  # on lance la boucle devolution

                print(f"Repetion {i}/{self.repeat}, meilleur coût: {self.bestPath.getDistance()},"
                      f" meilleur trajet: {self.bestPath.getRouteId()}")
                plt.gcf().savefig(
                    f"Répétition {i}.png")  # enregistrer le dernier affichage du graph (le meilleur path trouvé au bout de la simulation

                if final is None:
                    final = self.bestPath  # en enregistre le best path trouvé jusqu'a présent
                else:
                    if final.getDistance() > self.bestPath.getDistance():
                        final = self.bestPath  # on le remplace si un meilleur path est trouvé
        self.fermeture()
        plt.close('all')

    def fermeture(self):
        self.run = False

    # méthode utilisée pour calibrer le nombre d'individus dans la population avec un pourcentage d'erreur de 2%
    def calibrage(self):
        if self.nbIndividu * 0.98 < self.population.getSize() < self.nbIndividu * 1.02:
            self.bornRate = 50
            self.deathRate = 50
        else:
            if self.population.getSize() > self.nbIndividu:
                self.bornRate = 25
                self.deathRate = 35
            if self.population.getSize() < self.nbIndividu:
                self.bornRate = 35
                self.deathRate = 25

    # déclare le nombre d'individus souhaité avoir dans la population, cela peut entre changé au cours de la simulation
    def setNbIndividu(self, nb):
        self.nbIndividu = nb

    # déclare le pourcentage de mutation souhaitée avoir dans l'évolution, cela peut entre changé au cours de la simulation
    def setMutationRate(self, m):
        self.mutationRate = m

    # méthode qui gére evolution de la population
    def evolution(self):
        for i in range(0, self.finalGeneration):
            if self.run is False:  # tourner tant que le programme n'est pas fermé
                break
            else:
                self.generation += 1

                # calibrer quand cela est nécessaire (en cas de changement de paramétres)
                self.calibrage()

                self.setRanks()

                # -- extinction des individus faibles --
                dead = self.extinction()

                # --reproduction des individus forts--
                newborns = self.reproduction()

                # on fait exprès de supprimer et ajouter tout d'un coup pour ne pas dérégler les calculs de classement
                # supprimer tous les individus à tuer
                for p in dead:
                    self.population.removePath(p)
                    del p

                # ajouter tous les individus nés
                for c in newborns:
                    self.population.addPath(c)

                # dessine le graphe
                self.draw()

    # méthode qui classe les individus selon leur fitness, résultat sous format dictionnaire, rang : individu
    def setRanks(self):
        rank = {}
        for i in range(0, self.population.getSize()):
            rank[i] = self.population.paths[i].getFitness()
        self.rankPaths = sorted(rank.items(), key=operator.itemgetter(1), reverse=True)
        self.bestPath = self.population.getPaths()[self.rankPaths[0][0]]

    # méthode pour faire reproduire les meilleurs individus selon leur classement
    def reproduction(self):
        newborns = []
        couple = []

        # Attribution des poids de reproduction en fonction du classement
        poids_reproduction = [i * 50 for i in range(len(self.rankPaths))]
        poids_reproduction.reverse()

        # On choisit un pere et une mere de façon au hasard, mais en tenant compte des poids attribués les poids sont
        # là pour uniquement pour augmenter les chances d'être choisis, dans certains cas rares, il se peut que le
        # 3eme sera choisi plus de fois que le 1er, cela pour but de simuler une vraie reproduction naturelle
        for _ in range(0, int(len(self.rankPaths) / 100 * self.bornRate)):
            id_father = random.choices(self.rankPaths, weights=poids_reproduction, k=1)[0][0]
            id_mother = random.choices(self.rankPaths, weights=poids_reproduction, k=1)[0][0]

            # On s'assure que le père et la mére soient deux individus distincts et qu'ils n'ont jamais procréé ensemble
            # On évite d'avoir la meme paire de parents afin de ne pas avoir les mêmes individus "jumeaux"
            while id_father == id_mother or (id_father, id_mother) in couple or (id_mother, id_father) in couple:
                id_father = random.choices(self.rankPaths, weights=poids_reproduction, k=1)[0][0]
                id_mother = random.choices(self.rankPaths, weights=poids_reproduction, k=1)[0][0]

            couple.append((id_father, id_mother))

            father = self.population.getPaths()[id_father]
            mother = self.population.getPaths()[id_mother]

            # l'enfant va hériter du génome de ses paires comme ceci :
            # la premiére moitié viendra directement du pére
            startPos = 0
            endPos = int(len(self.population.cities) / 2)
            route = [None] * len(self.population.cities)
            for i in range(0, len(self.population.cities)):
                if startPos < endPos and startPos < i < endPos:
                    route[i] = father.getCity(i)
                elif startPos > endPos:
                    if not (startPos > i > endPos):
                        route[i] = mother.getCity(i)

            # la moitié restante sera complétée selon l'ordre des villes manquantes à partir du génome de la mére
            for i in range(0, len(self.population.cities)):
                if mother.getCity(i) not in route:
                    for ii in range(0, len(self.population.cities)):
                        if route[ii] is None:
                            route[ii] = mother.getCity(i)
                            break

            child = Path()
            child.setRoute(route)  # on définit le trajet de l'enfant
            child.mutation(self.mutationRate)  # on mute le génome obtenu de l'enfant
            newborns.append(child)

        return newborns

    # méthode d'extinction, elle tue directement la moitié des pires individus
    def extinction(self):
        dead = []
        for k in range(0, int(len(self.rankPaths) / 100 * self.deathRate)):
            p = self.population.getPaths()[self.rankPaths[len(self.rankPaths) - 1 - k][0]]
            dead.append(p)
        return dead

    # méthode pour dessiner le graphe avec networksxz et matplotlib
    def draw(self):
        # si aucune fenêtre n'est détecté ou que la fenêtre a été précédemment fermée, on la recrée
        if not plt.get_fignums():
            plt.figure(num="Affichage Du graph", figsize=(10, 6))
            # lie la touche ECHAP à la fenêtre, si on fait ECHAP l'algorithme s'arrête net
            plt.gcf().canvas.mpl_connect('key_press_event',
                                         lambda event: self.fermeture() if event.key == 'escape' else None)

        plt.cla()  # clear/effacer l'affichage précedent
        self.graph.clear()  # supprimer l'ancien graph

        pos = {}  # on crée les nœuds (villes) et les relient avec les arêtes selon la route du meilleur individu
        for i in range(-1, len(self.bestPath.getRoute()) - 1):
            city1 = self.bestPath.getRoute()[i]
            city2 = self.bestPath.getRoute()[i + 1]
            distance = city1.calcul_Distance(city2)
            self.graph.add_node(city1.getId(), label=str(city1.getId()))
            self.graph.add_node(city2.getId(), label=str(city2.getId()))
            # lier les deux villes
            self.graph.add_edge(city1.getId(), city2.getId(), weight=format(distance, '.2f'))
            pos[city1.getId()] = city1.getPosition()
            pos[city2.getId()] = city2.getPosition()

        labels_edges = {edge: self.graph.edges[edge]['weight'] for edge in self.graph.edges}

        liste = list(self.graph.nodes(data='label'))
        labels_nodes = {}
        for noeud in liste:
            labels_nodes[noeud[0]] = noeud[1]

        # nodes
        nx.draw_networkx_nodes(self.graph, pos, node_size=200, node_color='cyan', alpha=0.5)

        # labels
        nx.draw_networkx_labels(self.graph, pos, labels=labels_nodes, font_size=10,
                                font_color='black')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels_edges, font_color='red')

        nx.draw_networkx_edges(self.graph, pos, style="dashed", width=1)

        plt.text(0, -0.1, f"Nombre d'individus: {self.population.getSize()}, "
                          f"Pourcentage mutation: {self.mutationRate}%, "
                          f"Coût moyen: {round(self.population.getAverageDistance(), 2)}, "
                          f"\ntrajet meilleur individu: {self.bestPath.getRouteId()}",
                 fontsize=10, transform=plt.gca().transAxes)

        plt.title(f'Génération: {self.generation}, meilleur coût: {round(self.bestPath.getDistance(), 2)}')
        plt.gcf().canvas.flush_events()
        time.sleep(0.001)



# la class qui gére le programme dans son ensemble
# site le paramétre "list" est null le programme générera des villes aléatoire, sinon il prendra les villes depuis la liste en paramétre
class Program:
    def __init__(self, list=None):
        self.generation = 300
        self.mutation = 9
        self.repetition = 5
        self.nbCities = 15
        self.nbInitialPath = 300
        self.GA = None
        self.cities = list
        self.population = None

    # modifie les paramétrages du programme selon les saisies de l'utilisateur sur la fenêtre
    def calibre(self, event=None):
        if entree0.get().strip().isdigit():
            self.nbInitialPath = int(eval(entree0.get()))
        if entree3.get().strip().isdigit():
            self.mutation = int(eval(entree3.get()))
        if entree4.get().strip().isdigit():
            self.generation = int(eval(entree4.get()))
        if entree5.get().strip().isdigit():
            self.nbCities = int(eval(entree5.get()))
        if entree6.get().strip().isdigit():
            self.repetition = int(eval(entree6.get()))

        # si aucun algo n'est en cours, on supprime toutes les instances des différents objets créés pour libérer la ram
        if self.GA is None or self.GA.run is False:
            Population.supprimer_toutes_instances()
            GeneticAlgorith.supprimer_toutes_instances()
            Path.supprimer_toutes_instances()
            ville.supprimer_toutes_instances()

        # si l'algorithme est en cours alors, on vient modifier directement le paramétrage dessus
        else:
            self.GA.setNbIndividu(int(eval(entree0.get())))
            self.GA.setMutationRate(int(eval(entree3.get())))
            self.GA.finalGeneration = self.generation
            if not self.population.choix and check_var.get() == 1:
                self.GA.choix = True
            elif self.population.choix and check_var.get() == 0:
                self.GA.choix = False

    # méthode pour commencer l'algo
    def start(self):
        plt.close("start")
        # on vérifie qu'aucun algo n'est déjà en cours (on évite de lancer plusieurs d'un coup)
        if self.GA is None or self.GA.run is False:
            if self.GA is not None: # on supprime le dernier algo qui s'est terminé pour libérer la mémoire
                Population.supprimer_toutes_instances()
                GeneticAlgorith.supprimer_toutes_instances()
                Path.supprimer_toutes_instances()
                ville.supprimer_toutes_instances()

            self.population = Population(self.cities, self.nbCities)
            programme.calibre()
            self.GA = GeneticAlgorith(self.population, self.generation, self.repetition, self.nbInitialPath,
                                      50, 50, self.mutation)
            programme.calibre()
            self.GA.start()


# ------------main------------
if __name__ == '__main__':

    city1 = ville(60, 200, 0)
    city2 = ville(180, 200, 1)
    city3 = ville(80, 180, 2)
    city4 = ville(140, 180, 3)
    city5 = ville(20, 160, 4)
    city6 = ville(100, 160, 5)
    city7 = ville(200, 160, 6)
    city8 = ville(140, 140, 7)
    city9 = ville(40, 120, 8)
    city10 = ville(100, 120, 9)
    city11 = ville(180, 100, 10)
    city12 = ville(60, 80, 11)
    city13 = ville(120, 80, 12)
    city14 = ville(180, 60, 13)
    city15 = ville(20, 40, 14)
    city16 = ville(100, 40, 15)
    city17 = ville(200, 40, 16)
    city18 = ville(20, 20, 17)
    city19 = ville(60, 20, 18)
    city20 = ville(160, 20, 19)

    liste = [city1, city2, city3, city4, city5, city6, city7, city8, city9, city10, city11, city12,
             city13, city14, city15, city16, city17, city18, city19]


    def on_closing():
        if tk.messagebox.askokcancel("Quitter", "Êtes-vous sûr de vouloir quitter ?"):
            plt.close('all')
            if programme.GA:
                programme.GA.fermeture()
            fen1.destroy()


    # programme "principal"
    programme = Program()
    fen1 = tk.Tk("Agg")

    # BOUTON START
    b1 = tk.Button(fen1, text='Start', command=programme.start)
    b1.grid(row=0, column=0, padx=5, pady=0)

    # Entrée pour le nombre d'individus
    entree0 = tk.Entry(fen1)
    entree0.bind("<Return>", programme.calibre)
    entree0.insert(0, str(programme.nbInitialPath))
    entree0.grid(row=2, column=1)

    chaine0 = tk.Label(fen1)
    chaine0.configure(text="nombre d'individu")
    chaine0.grid(row=3, column=1)

    # Entrée pour le pourcentage de mutation
    entree3 = tk.Entry(fen1)
    entree3.bind("<Return>", programme.calibre)
    entree3.insert(0, str(programme.mutation))
    entree3.grid(row=2, column=2)

    chaine3 = tk.Label(fen1)
    chaine3.configure(text="Pourcentage de mutation")
    chaine3.grid(row=3, column=2)

    # Entrée pour le nombre de génération
    entree4 = tk.Entry(fen1)
    entree4.bind("<Return>", programme.calibre)
    entree4.insert(0, str(programme.generation))
    entree4.grid(row=2, column=3)

    chaine4 = tk.Label(fen1)
    chaine4.configure(text="Nombre de génération")
    chaine4.grid(row=3, column=3)

    # Entrée pour le nombre de villes
    entree5 = tk.Entry(fen1)
    entree5.bind("<Return>", programme.calibre)
    entree5.insert(0, str(programme.nbCities))
    entree5.grid(row=0, column=2)

    chaine5 = tk.Label(fen1)
    chaine5.configure(text="Nombre de villes")
    chaine5.grid(row=1, column=2)

    # Entrée pour le nombre de simulation
    entree6 = tk.Entry(fen1)
    entree6.bind("<Return>", programme.calibre)
    entree6.insert(0, str(programme.repetition))
    entree6.grid(row=0, column=1)

    chaine6 = tk.Label(fen1)
    chaine6.configure(text="Nombre de simulation")
    chaine6.grid(row=1, column=1)

    # Création d'une variable Tkinter pour stocker l'état de la case à cocher
    check_var = tk.IntVar()
    # Création de la case à cocher
    check_button = tk.Checkbutton(fen1, text="Actif: Utilise le poids\n sinon Utilise la distance", variable=check_var,
                                  command=programme.calibre)
    check_button.grid(row=0, column=3)

    # Associer la fonction on_closing() à l'événement de fermeture de la fenêtre
    fen1.protocol("WM_DELETE_WINDOW", on_closing)

    plt.figure(num="start")

    # Exécution de la boucle principale
    fen1.mainloop()
