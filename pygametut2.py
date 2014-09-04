import random
import pygame as pg
from pygame.locals import *
import math
import textwrap
import shelve

pg.init()
PLAYER_IMAGE = 'data\images\snake.png'
WALL_IMAGE = 'data\images\wall.png'
GRASS_IMAGE = 'data\images\grass.png'

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30

colors = {
		'green':(0,205,0),
		'blue':(0,0,205),
		'red':(205,0,0),
		'black':(0,0,0),
		'white':(250,250,250)
		}
		
BGCOLOR = colors['black']

#screen sizing
TILE_SIZE = 25
MAP_SIZE = 35
map = []
LIMIT_FPS = 30
fpsClock = pg.time.Clock()
window = pg.display.set_mode((TILE_SIZE*MAP_SIZE,(TILE_SIZE*MAP_SIZE + 50)))

