# Implementar Dear PyGUI para la visualizacion de datos

import pygame
import pygame_gui
import sys
from config import *
from sp import *
from entity import *

def smooth_curve(data, window=5):
    if len(data) < window:
        return data

    smoothed = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        avg = sum(data[start:i+1]) / (i - start + 1)
        smoothed.append(avg)
    return smoothed

def draw_convergence_graph(screen, fitness_history, rect):
    if len(fitness_history) < 2:
        return

    x, y, w, h = rect
    pygame.draw.rect(screen, BLACK, rect, 2)

    smoothed = smooth_curve(fitness_history, window=7)
    max_fitness = max(smoothed)
    if max_fitness == 0:
        return

    points=[]
    for i,fitness in enumerate(smoothed):
        px=x+(i/(len(smoothed)-1))*w
        py=y+h-(fitness / max_fitness)*h
        points.append((px, py))

    pygame.draw.lines(screen,(200,0,0),False,points,2)

def draw_text(screen,text,x,y,color=(0,0,0)):
    surface=FONT.render(text,True,color)
    screen.blit(surface,(x,y))

def draw_individual_genes(screen,ind,x,y):
    if ind is None:
        return
    line=0
    lh=18

    draw_text(screen,"Mejor individuo (genes):", x, y)
    line+=1
    draw_text(screen,f"Speed: {ind.speed:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Radio detección: {ind.radio_deteccion:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"N° peligros: {ind.num_peligros}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Fuerza evasión: {ind.fuerza_evasion:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Peso peligro cercano: {ind.peso_peligro_cercano:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Inercia movimiento: {ind.inercia_movimiento:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Peso centro: {ind.peso_centro:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Zona confort centro: {ind.zona_confort_centro:.2f}", x, y + line * lh)
    line+=1
    draw_text(screen,f"Radio: {ind.radius:.2f}", x, y + line * lh)

pygame.font.init()
FONT=pygame.font.SysFont("arial", 16)

def main():
    global TASA_MUTACION
    pygame.init()

    screen = pygame.display.set_mode((WIDTH_TOTAL, HEIGHT))
    pygame.display.set_caption("Algoritmo Genético")
    clock = pygame.time.Clock()

    # ---------- pygame_gui ----------
    ui_manager = pygame_gui.UIManager((WIDTH_TOTAL, HEIGHT))

    # ---------- VARIABLES ----------
    fitness_history = []
    generacion = 1
    poblacion = crear_poblacion()
    peligros = []
    wave = 1
    time_since_wave = 0.0
    running = True
    paused = False

    time_scale = 1.0
    best_fitness_global = -float("inf")
    best_individual_global = None

    # ---------- UI ELEMENTS ----------
    panel_x = WIDTH_SIM + 10

    label_gen = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 220, WIDTH_PANEL - 20, 25),
        "Generación: 1",
        ui_manager
    )

    label_mut = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 240, WIDTH_PANEL - 20, 25),
        f"Tasa mutación: {TASA_MUTACION}",
        ui_manager
    )

    label_best = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 260, WIDTH_PANEL - 20, 25),
        "Mejor fitness: 0.00",
        ui_manager
    )

    

    label_time = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 320, WIDTH_PANEL - 20, 25),
        "Tiempo:",
        ui_manager
    )
    slider_time = pygame_gui.elements.UIHorizontalSlider(
        pygame.Rect(panel_x, 340, WIDTH_PANEL - 20, 25),
        start_value=time_scale,
        value_range=(1.0, 20.0),
        manager=ui_manager
    )

    # Genes
    label_besto= pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 380, WIDTH_PANEL - 20, 25),
        "MEJOR INDIVIDUO",
        ui_manager
    )
    label_vel = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 400, WIDTH_PANEL - 20, 25),
        "Velocidad: 0.00",
        ui_manager
    )
    label_detec = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 420, WIDTH_PANEL - 20, 25),
        "Radio de deteccion: 0",
        ui_manager
    )
    label_pel = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 440, WIDTH_PANEL - 20, 25),
        "Numero de proyectiles: 0",
        ui_manager
    )
    label_rad = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 460, WIDTH_PANEL - 20, 25),
        "Radio: 0",
        ui_manager
    )
    label_rad_confort = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 480, WIDTH_PANEL - 20, 25),
        "Radio zona de confort: 0",
        ui_manager
    )
    label_peso_centro = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 500, WIDTH_PANEL - 20, 25),
        "Peso centro: 0.00",
        ui_manager
    )
    label_inercia = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 520, WIDTH_PANEL - 20, 25),
        "Inercia: 0.00",
        ui_manager
    )
    label_evac = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 540, WIDTH_PANEL - 20, 25),
        "Fuerza de evasion: 0.00",
        ui_manager
    )
    label_pel_cercano = pygame_gui.elements.UILabel(
        pygame.Rect(panel_x, 560, WIDTH_PANEL - 20, 25),
        "Peso peligro cercano: 0.00",
        ui_manager
    )

    # ---------- LOOP PRINCIPAL ----------
    while running:
        dt = clock.tick(FPS) / 1000

        if paused:
            scaled_dt = 0
        else:
            scaled_dt = dt * time_scale

        remaining_time = scaled_dt

        # ---------- SIMULACIÓN ----------
        while remaining_time > 0:
            step = min(remaining_time, MAX_DT)
            time_since_wave += step

            # Oleadas
            if time_since_wave >= WAVE_INTERVAL:
                time_since_wave = 0.0
                bolitas_por_pared = 1 + (wave // 3)
                for _ in range(bolitas_por_pared * 4):
                    peligros.append(spawn_peligro())
                if wave<20:
                    wave+=1

            # Individuos
            for ind in poblacion:
                if not ind.alive:
                    continue

                ind.update(step, peligros)

                for p in peligros:
                    if check_collision(ind, p):
                        ind.alive = False
                        ind.calculate_fitness()
                        break

            # Peligros
            for p in peligros:
                p.update(step)

            peligros = [p for p in peligros if p.alive]
            remaining_time -= step

        # ---------- EVENTOS ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            ui_manager.process_events(event)

            if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:

                if event.ui_element == slider_time:
                    time_scale = event.value
                    label_time.set_text(
                        f"Tiempo: x{time_scale:.1f}"
                    )

        # ---------- FIN DE GENERACIÓN ----------
        if all(not ind.alive for ind in poblacion):

            for ind in poblacion:
                if ind.fitness is None:
                    ind.calculate_fitness()

            best_individual = max(poblacion, key=lambda i: i.fitness)
            best_fitness = best_individual.fitness
            fitness_history.append(best_fitness)

            if best_fitness > best_fitness_global:
                best_fitness_global = best_fitness
                best_individual_global = best_individual

            print(
                f"Generación {generacion} | "
                f"Mejor fitness: {best_fitness:.2f}"
            )

            poblacion = nueva_generacion(poblacion)
            peligros.clear()
            wave = 1
            time_since_wave = 0.0
            generacion += 1

            label_gen.set_text(f"Generación: {generacion}")
            label_best.set_text(
                f"Mejor fitness: {best_fitness_global:.2f}"
            )
            label_vel.set_text(f"Velocidad: {best_individual_global.speed:.2f}")
            label_detec.set_text(f"Radio de deteccion: {best_individual_global.radio_deteccion:.0f}")
            label_pel.set_text(f"Numero de proyectiles: {best_individual_global.num_peligros:.0f}")
            label_rad.set_text(f"Radio: {best_individual_global.radius:.0f}")
            label_rad_confort.set_text(f"Radio zona de confort: {best_individual_global.zona_confort_centro:.0f}")
            label_peso_centro.set_text(f"Peso centro: {best_individual_global.peso_centro:.2f}")
            label_inercia.set_text(f"Inercia: {best_individual_global.inercia_movimiento:.2f}")
            label_evac.set_text(f"Fuerza de evasion: {best_individual_global.fuerza_evasion:.2f}")
            label_pel_cercano.set_text(f"Peso peligros cercanos: {best_individual_global.peso_peligro_cercano:.2f}")


        # ---------- RENDER ----------
        screen.fill(WHITE)

        # Área simulación
        pygame.draw.rect(screen, WHITE, (0, 0, WIDTH_SIM, HEIGHT))
        pygame.draw.rect(screen, GRAY, (0, 0, WIDTH_SIM, HEIGHT), 3)

        # Panel lateral
        pygame.draw.rect(
            screen,
            (230, 230, 230),
            (WIDTH_SIM, 0, WIDTH_PANEL, HEIGHT)
        )

        # Gráfica
        graph_rect = (
            WIDTH_SIM + 20,
            20,
            WIDTH_PANEL - 40,
            200
        )
        draw_convergence_graph(
            screen,
            fitness_history,
            graph_rect
        )

        pygame.draw.rect(
            screen,
            GRAY,
            (WIDTH_SIM, 0, WIDTH_PANEL, HEIGHT),
            3
        )

        # Dibujar peligros
        for p in peligros:
            if p.pos.x < WIDTH_SIM:
                p.draw(screen)

        # Dibujar individuos vivos
        for ind in poblacion:
            if ind.alive:
                ind.draw(screen)

        # ---------- UI ----------
        ui_manager.update(dt)
        ui_manager.draw_ui(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()

#########################