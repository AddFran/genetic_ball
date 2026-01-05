import pygame
from config import *
import random
from sp import *

# Hacemos uso de vectores para representar los mov de los bichos

class Individuo:
    def __init__(self,x,y):
        self.pos=pygame.Vector2(x,y)
        #self.radius=PLAYER_RADIUS # 8

        # Genes con los intervalos permitidos
        self.speed                =random.uniform(80,200)   # pixeles/segundo
        self.velocity             =pygame.Vector2(0,0)      # speed y velocity forman un solo gen
        self.radio_deteccion      =random.uniform(60,200)   # Hasta donde puede ver
        self.num_peligros         =random.randint(1,20)     # Numero de peligros que puede ver al mismo timepo
        self.fuerza_evasion       =random.uniform(1.0,3.0)  # Reaccion, que tan fuerte huye (1: huida suave / 2: huida agresiva)
        self.peso_peligro_cercano =random.uniform(1.0,2.5)  # Que tan miedoso es el individuo
        self.inercia_movimiento   =random.uniform(0.0,0.9)  # Reflejos, + inercia se tarda en decidir, - inercia movimientos instantaneos
        self.peso_centro          =random.uniform(1.0,2.0)  # Intensidad con la que quedra regresar al centro
        self.zona_confort_centro  =random.uniform(50,100)   # Si el bicho sale de esta zona, entonces afecta su rumbo intentando regresar (todo eso en calcular_vector_centro)
        self.radius               =random.randint(4,12)

        # Info extra
        self.alive=True
        self.color=BLUE
        self.time_alive=0.0
        self.fitness=0.0

    def update(self,dt,peligros):
        vector_evasion=self.calcular_vector_evasion(peligros)
        vector_centro=self.calcular_vector_centro()

        vector_resultante=vector_evasion+vector_centro

        if vector_resultante.length()>0:
            vector_resultante.normalize_ip() # Direccion general tras conciderar los peligros y el centro

        # Mezcla con inercia (vectores con vectores)
        self.velocity=(self.velocity*self.inercia_movimiento            # Velocidad que ya tenia
                       +vector_resultante*(1-self.inercia_movimiento))  # Nueva velocidad

        if self.velocity.length()>0:
            self.velocity.scale_to_length(self.speed)

        self.pos+=self.velocity*dt

        # Limitar dentro del escenario
        self.pos.x=max(self.radius,min(WIDTH-self.radius,self.pos.x))
        self.pos.y=max(self.radius,min(HEIGHT-self.radius,self.pos.y))

        # Muerte si se pasa de gracioso (se va a las esquinas)
        if(
            self.pos.x<=self.radius or
            self.pos.x>=WIDTH-self.radius or
            self.pos.y<=self.radius or
            self.pos.y>=HEIGHT-self.radius
        ):
            self.alive=False
            self.calculate_fitness() 
            return

        self.time_alive += dt

    # Ppor el momento el fitness solo es el tiempo vivo
    def calculate_fitness(self):
        self.fitness=self.time_alive 

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )
    def calcular_vector_evasion(self,peligros):
        amenazas=detectar_peligros(self,peligros)
        if not amenazas:
            return pygame.Vector2(0,0)

        evasion=pygame.Vector2(0,0)

        for p,dist in amenazas:
            # Vector desde el peligro hacia el individuo
            direccion=self.pos-p.pos # A - B = vector que apunta de B hacia A

            if direccion.length()==0:
                continue

            direccion.normalize_ip() # Normaliza un vector, lo reduce a su vector unitario, es decir, a solo indicar direccion

            # Peso: mas cerca mas fuerte
            peso=self.peso_peligro_cercano/max(dist,1)
            evasion+=direccion*peso # Cada peligro genera su propio vector indicando a donde debe ir el individuo, el peso ajusta la intensidad
        return evasion*self.fuerza_evasion
    
    def calcular_vector_centro(self):
        centro=pygame.Vector2(WIDTH/2,HEIGHT/2)
        direccion=centro-self.pos
        distancia=direccion.length()

        if distancia==0:
            return pygame.Vector2(0,0)

        if distancia<self.zona_confort_centro:
            return pygame.Vector2(0,0)

        direccion.normalize_ip()

        fuerza=(distancia/(WIDTH/2))*self.peso_centro # Con (distancia/(WIDTH/2)) normalizacmos la distancia (0 a 1), asignando un valor segun la distancia al centro
        return direccion*fuerza

class Peligro:
    def __init__(self, pos, velocity):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.radius = random.randint(4,10)
        self.alive = True

    def update(self,dt):
        self.pos+=self.velocity * dt
        if (
            self.pos.x<-self.radius or
            self.pos.x>WIDTH_SIM+self.radius or
            self.pos.y<-self.radius or
            self.pos.y>HEIGHT+self.radius
        ):
            self.alive=False


    def draw(self,screen):
        pygame.draw.circle(
            screen,
            BLACK,
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )


def detectar_peligros(individuo,peligros):
    cercanos=[]

    for p in peligros:
        dist=individuo.pos.distance_to(p.pos)
        if dist<=individuo.radio_deteccion:
            cercanos.append((p, dist))

    # Ordenar por cercania
    cercanos.sort(key=lambda x: x[1])

    # Limitar numero de peligros considerados
    return cercanos[:individuo.num_peligros]



#########################################################################################

def spawn_peligro():
    wall=random.choice(["top","bottom","left","right"])
    if wall=="top":
        pos=pygame.Vector2(random.randint(0,WIDTH),0)
        direction=pygame.Vector2(0,1)
    elif wall=="bottom":
        pos=pygame.Vector2(random.randint(0,WIDTH),HEIGHT)
        direction=pygame.Vector2(0,-1)
    elif wall=="left":
        pos=pygame.Vector2(0,random.randint(0,HEIGHT))
        direction=pygame.Vector2(1,0)
    else:  # right
        pos=pygame.Vector2(WIDTH_SIM,random.randint(0,HEIGHT))
        direction=pygame.Vector2(-1,0)

    speed=random.uniform(100,200)  # pixeles por segundo
    velocity=direction.normalize()*speed

    return Peligro(pos,velocity)

def check_collision(individuo,peligro):
    dist=individuo.pos.distance_to(peligro.pos)
    return dist<(individuo.radius+peligro.radius)

def crear_poblacion():
    poblacion=[]
    for _ in range(POPULATION_SIZE):
        poblacion.append(Individuo(WIDTH//2,HEIGHT//2))
    return poblacion

def seleccion_ruleta(poblacion):
    total_fitness=sum(ind.fitness for ind in poblacion)
    if total_fitness==0:
        return random.choice(poblacion)
    r=random.uniform(0,total_fitness)
    acumulado=0.0
    for ind in poblacion:
        acumulado += ind.fitness
        if acumulado >= r:
            return ind
    return poblacion[-1]

def cruzar(padre1,padre2):
    hijo=Individuo(WIDTH//2,HEIGHT//2)

    hijo.speed               =padre1.speed
    hijo.radio_deteccion     =padre1.radio_deteccion
    hijo.num_peligros        =padre1.num_peligros
    hijo.fuerza_evasion      =padre1.fuerza_evasion
    hijo.radius              =padre1.radius

    hijo.peso_peligro_cercano=padre2.peso_peligro_cercano 
    hijo.inercia_movimiento  =padre2.inercia_movimiento
    hijo.peso_centro         =padre2.peso_centro 
    hijo.zona_confort_centro =padre2.zona_confort_centro
    

    return hijo

# Cambiar a uno donde se verifique de gen a gen, no todo el individuo
def mutar(individuo):
    choice=random.randint(1,9)
    if choice==1:
        individuo.speed=random.uniform(80,200)
    if choice==2:
        individuo.radio_deteccion=random.uniform(60,200)
    if choice==3:
        individuo.num_peligros=random.randint(1,20)
    if choice==4:
        individuo.fuerza_evasion=random.uniform(1.0,3.0)
    if choice==5:
        individuo.peso_peligro_cercano=random.uniform(1.0,2.5)
    if choice==6:
        individuo.inercia_movimiento=random.uniform(0.0,0.9)
    if choice==7:
        individuo.peso_centro=random.uniform(0.5,2.0)
    if choice==8:
        individuo.zona_confort_centro=random.uniform(50,200)
    if choice==9:
        individuo.radius=random.randint(4,12)

def mutar2(individuo,tasa=TASA_MUTACION):
    if random.random()<tasa:
        individuo.speed=random.uniform(80,200)
    if random.random()<tasa:
        individuo.radio_deteccion=random.uniform(60,200)
    if random.random()<tasa:
        individuo.num_peligros=random.randint(1,20)
    if random.random()<tasa:
        individuo.fuerza_evasion=random.uniform(1.0,3.0)
    if random.random()<tasa:
        individuo.peso_peligro_cercano=random.uniform(1.0,2.5)
    if random.random()<tasa:
        individuo.inercia_movimiento=random.uniform(0.0,0.9)
    if random.random()<tasa:
        individuo.peso_centro=random.uniform(0.5,2.0)
    if random.random()<tasa:
        individuo.zona_confort_centro=random.uniform(50,200)
    if random.random()<tasa:
        individuo.radius=random.randint(4,12)

def nueva_generacion(poblacion):
    poblacion.sort(key=lambda x: x.fitness,reverse=True)
    nueva=[]

    # Si se queda el mejor de lo mejor en cada generacion
    for i in range(3):
        elite=poblacion[i]
        #elite.fitness=0.0
        nueva.append(elite)
    
    #elite=poblacion[0]
    ##elite.fitness=0.0
    #nueva.append(elite)

    flag=True
    while len(nueva)<POPULATION_SIZE:
        p1=seleccion_ruleta(poblacion)
        p2=seleccion_ruleta(poblacion)

        if flag==True:
            hijo=cruzar(p1,p2)
            flag=False
        else:
            hijo=cruzar(p2,p1)
            flag=True

        if random.random()<TASA_MUTACION:
            mutar(hijo)
            print("Se ha producido una mutacion")

        nueva.append(hijo)

    return nueva