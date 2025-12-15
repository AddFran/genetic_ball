import pygame
import sys
from config import *
from sp import *
from entity import *

def draw_convergence_graph(screen, fitness_history, rect):
    if len(fitness_history) < 2:
        return

    x, y, w, h = rect

    # Marco
    pygame.draw.rect(screen, BLACK, rect, 2)

    max_fitness = max(fitness_history)
    if max_fitness == 0:
        return

    points = []
    for i, fitness in enumerate(fitness_history):
        px = x + (i / (len(fitness_history) - 1)) * w
        py = y + h - (fitness / max_fitness) * h
        points.append((px, py))

    pygame.draw.lines(screen, (200, 0, 0), False, points, 2)

def draw_text(screen, text, x, y, color=(0, 0, 0)):
    surface = FONT.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_individual_genes(screen, ind, x, y):
    if ind is None:
        return

    line = 0
    lh = 18

    draw_text(screen, "Mejor individuo (genes):", x, y)
    line += 1

    draw_text(screen, f"Speed: {ind.speed:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Radio detección: {ind.radio_deteccion:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"N° peligros: {ind.num_peligros}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Fuerza evasión: {ind.fuerza_evasion:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Peso peligro cercano: {ind.peso_peligro_cercano:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Inercia movimiento: {ind.inercia_movimiento:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Peso centro: {ind.peso_centro:.2f}", x, y + line * lh)
    line += 1

    draw_text(screen, f"Zona confort centro: {ind.zona_confort_centro:.2f}", x, y + line * lh)

pygame.font.init()
FONT = pygame.font.SysFont("arial", 16)

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH_TOTAL, HEIGHT))
    pygame.display.set_caption("Algoritmo Genético")

    clock = pygame.time.Clock()

    # =======================
    # VARIABLES GENÉTICAS
    # =======================
    fitness_history = []
    generacion = 1

    poblacion = crear_poblacion()
    peligros = []

    wave = 1
    time_since_wave = 0.0

    running = True
    time_scale = 10.0

    best_fitness_global = -float("inf")
    best_individual_global = None

    # =======================
    # LOOP PRINCIPAL
    # =======================
    while running:

        dt = clock.tick(FPS) / 1000
        scaled_dt = dt * time_scale

        # =======================
        # SUBSTEPS (FIXED TIMESTEP)
        # =======================
        remaining_time = scaled_dt

        while remaining_time > 0:
            step = min(remaining_time, MAX_DT)
            time_since_wave += step

            # Oleadas de peligros
            if time_since_wave >= WAVE_INTERVAL:
                time_since_wave = 0.0

                bolitas_por_pared = 1 + (wave // 3)
                total = bolitas_por_pared * 4

                for _ in range(total):
                    peligros.append(spawn_peligro())

                wave += 1

            # Lógica de individuos
            for ind in poblacion:
                if not ind.alive:
                    continue

                ind.update(step, peligros)

                for p in peligros:
                    if check_collision(ind, p):
                        ind.alive = False
                        ind.calculate_fitness()
                        break

            # Actualizar peligros
            for p in peligros:
                p.update(step)

            # Eliminar peligros fuera del área
            peligros = [p for p in peligros if p.alive]

            remaining_time -= step

        # =======================
        # EVENTOS
        # =======================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # =======================
        # FIN DE GENERACIÓN
        # =======================
        if all(not ind.alive for ind in poblacion):

            # Seguridad: fitness final
            for ind in poblacion:
                if ind.fitness is None:
                    ind.calculate_fitness()

            # Mejor individuo de la generación
            best_individual = max(poblacion, key=lambda i: i.fitness)
            best_fitness = best_individual.fitness

            fitness_history.append(best_fitness)

            # Mejor individuo global
            if best_fitness > best_fitness_global:
                best_fitness_global = best_fitness
                best_individual_global = best_individual

            print(
                f"Generación {generacion} | "
                f"Mejor fitness: {best_fitness:.2f}"
            )

            # Nueva generación
            poblacion = nueva_generacion(poblacion)

            peligros.clear()
            wave = 1
            time_since_wave = 0.0
            generacion += 1

        # =======================
        # RENDER
        # =======================
        screen.fill(WHITE)

        # Área de simulación
        pygame.draw.rect(screen, WHITE, (0, 0, WIDTH_SIM, HEIGHT))
        pygame.draw.rect(screen, GRAY, (0, 0, WIDTH_SIM, HEIGHT), 3)

        # Panel lateral
        pygame.draw.rect(
            screen,
            (230, 230, 230),
            (WIDTH_SIM, 0, WIDTH_PANEL, HEIGHT)
        )

        # Gráfica de convergencia
        graph_rect = (
            WIDTH_SIM + 20,
            20,
            WIDTH_PANEL - 40,
            200
        )
        draw_convergence_graph(screen, fitness_history, graph_rect)

        # =======================
        # TEXTO DEL PANEL
        # =======================
        text_x = WIDTH_SIM + 20
        text_y = 240
        line_height = 22

        draw_text(
            screen,
            f"Generación actual: {generacion}",
            text_x,
            text_y
        )

        draw_text(
            screen,
            f"Tasa de mutación: {TASA_MUTACION:.3f}",
            text_x,
            text_y + line_height
        )

        draw_text(
            screen,
            f"Mejor fitness histórico: {best_fitness_global:.2f}",
            text_x,
            text_y + 2 * line_height
        )

        # =======================
        # GENES DEL MEJOR INDIVIDUO
        # =======================
        genes_y = text_y + 4 * line_height

        if best_individual_global:
            draw_individual_genes(
                screen,
                best_individual_global,
                text_x,
                genes_y
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

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


#########################