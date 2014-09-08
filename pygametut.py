import random
import pygame as pg
from pygame.locals import *
import math
import textwrap
import shelve
import os


pg.init()
#linux
PLAYER_IMAGE = os.path.join("data","images","snake.png")
WALL_IMAGE = os.path.join("data","images","wall.png")
GRASS_IMAGE = os.path.join("data","images","grass.png")
TROLL_IMAGE = os.path.join("data","images","troll.png")
ORC_IMAGE = os.path.join("data","images","orc.png")
SLIME_IMAGE = os.path.join("data","images","slime.png")
SKELETON_IMAGE = os.path.join("data","images","skeleton.png")

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30
MAX_ROOM_MONSTERS=3

fullscreen = False

colors = {
			'green':(0,205,0),
			'blue':(0,0,205),
			'red':(205,0,0),
			'black':(0,0,0)
			}

BGCOLOR = colors['black']

#SCREEN SIZING
TILE_SIZE = 28
MAP_SIZE = 35
map = []
LIMIT_FPS = 30
fpsClock = pg.time.Clock()
window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE))
class Tile:
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		self.explored = False
		self.size_x, self.size_y = TILE_SIZE, TILE_SIZE
		
		
		#by default, tile is blocked if blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

class Rect:
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
		
	def center(self):
		center_x = (self.x1 + self.x2) /2
		center_y = (self.y1 + self.y2) /2
		return (center_x, center_y)
		
	def intersect(self, other):
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
					self.y1 <= other.y2 and self.y2 >= other.y1)
		
class Object:
	def __init__(self, x, y, image,name, blocks=False):
		self.x = x
		self.y = y
		self.image = image
		self.surfaceImage = pg.image.load(image).convert()
		self.name = name
		self.blocks = blocks

	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy
		
	def draw(self):
		window.blit(self.surfaceImage, (self.x*TILE_SIZE, self.y*TILE_SIZE))
	
	def clear(self):
		window.fill(BGCOLOR,pg.Rect((self.x,self.y),(TILE_SIZE,TILE_SIZE)))

def place_monsters(room):
	#choose random number of monsters
	num_monsters = random.randint(0, MAX_ROOM_MONSTERS)

	for r in range(num_monsters):
		#choose random spot for this monster
		x = random.randint(room.x1, room.x2)
		y = random.randint(room.y1, room.y2)

		if not is_blocked(x, y):

			choice = random_percentage()

			if choice <10:
				#create an orc 10% chance
				monster = Object(x,y,ORC_IMAGE,"orc")
			elif choice <10+30:
				#create a troll 30% chance
				monster = Object(x,y,TROLL_IMAGE,"troll")
			elif choice < 10+30+10:
				#create skeleton 10% chance
				monster = Object(x,y,SKELETON_IMAGE,"skeleton")
			else:
				#create slime 50% chance
				monster = Object(x,y,SLIME_IMAGE,"slime")
			objects.append(monster)

def random_percentage():

	return (random.randint(0,100))

def create_room(room):
	global map
	for x in range(room.x1 + 1, room.x2 + 1):
		for y in range(room.y1 + 1, room.y2 + 1):
			map[x][y].blocked = False
			map[x][y].block_sight = False

def create_h_tunnel(x1,x2,y):
	global map
	for x in range(min(x1,x2),max(x1,x2)+1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def create_v_tunnel(y1,y2,x):
	global map
	for y in range(min(y1,y2),max(y1,y2)+1):
		map[x][y].blocked = False
		map[x][y].block_sight = False
		
def make_map():
	print "making map"
	global map
	
	map = [[Tile(True)
				for y in range(MAP_SIZE)]
					for x in range(MAP_SIZE)]
					
	rooms = []
	num_rooms = 0
	for r in range(MAX_ROOMS):
		print r
		w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		x = random.randint(0, MAP_SIZE - w - 1)
		y = random.randint(0, MAP_SIZE - h - 1)
		
		new_room = Rect(x, y, w, h)
		
		failed = False
		
		for other_room in rooms:
			print "room looping"
			
			if new_room.intersect(other_room):
				print "room intersect"
				
				failed = True
				break
				
		if not failed:
			print "first room created"
			
			create_room(new_room)
			(new_x, new_y) = new_room.center()
			if num_rooms == 0:
				player.x = new_x
				player.y = new_y
				#player.x = new_x
				#player.y = new_y
			
			else:
				place_monsters(new_room)
				#all rooms after the first
				(prev_x, prev_y) = rooms[num_rooms -1].center()
				
				if random.randint(0,1) == 1:
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)
			rooms.append(new_room)
			num_rooms += 1
	
def player_move_or_attack(dx, dy):
	
	x = player.x + dx
	y = player.y + dy

	#try to find an attackable object there
	target = None
	for object in objects:
		if object.x == x and object.y == y:
			target = object
			break

	#attack if target found, move otherwise
	if target is not None:
		print 'The ' + target.name + ' laughs at your puny efforts to attack'
	else:
		player.move(dx, dy)	
					
def render_all():
	#draw all objects
	
	for y in range(MAP_SIZE):
		for x in range(MAP_SIZE):
			wall = map[x][y].block_sight
			if wall == True:
				window.blit(wallSurface,(x*TILE_SIZE,y*TILE_SIZE))
			else:
				window.blit(grassSurface,(x*TILE_SIZE,y*TILE_SIZE))
				
	for object in objects:
		object.draw()

def is_blocked(x, y):
	#first test the map tile
	if map[x][y].blocked:
		return True

	#now check for any blocking objects
	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return True
	return False

def toggle_fullscreen():
	global window
	flags = window.get_flags()
	if flags&FULLSCREEN==False:
		print 'going fullscreen'
		window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE),
					pg.FULLSCREEN)
		fullscreen = True
	else:
		window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE))
		fullscreen = False

def handle_keys():
	player_choice = None
	keys = pg.event.get()
	for event in keys:
		if event.type == pg.QUIT:
			return 'exit'
		elif event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				return 'exit'
			elif ((event.key == K_RETURN) and 
							(event.mod&(KMOD_LALT|KMOD_RALT)) != 0):
				toggle_fullscreen()

			if game_state == 'playing':
				if event.key == K_RIGHT:
					player_move_or_attack(1,0)
					player_choice = 'moved'
				elif event.key == K_LEFT:
					player_move_or_attack(-1,0)
					player_choice = 'moved'
				elif event.key == K_UP:
					player_move_or_attack(0,-1)
					player_choice = 'moved'
				elif event.key == K_DOWN:
					player_move_or_attack(0,1)
					player_choice = 'moved'
				else:
					return 'noturntaken'

	if player_choice != 'moved':
		return 'noturntaken'
	#if not keys and not keys.KEYUP:
	#	return 'noturntaken'

#FUTURE FOV CALCULATION



#screen = pg.display.get_surface()			
#window.fill((0,205,0),pg.Rect((0,0),(50,50)))

player = Object(1,1,PLAYER_IMAGE,"player")
objects = [player]

make_map()
wallSurface = pg.image.load(WALL_IMAGE).convert()
grassSurface = pg.image.load(GRASS_IMAGE).convert()

pg.display.update()
playing = True

game_state = 'playing'
player_action = 'None'

while playing:
	window.fill(BGCOLOR)
	render_all()
	
	player_action = handle_keys()

	#print player_action

	if player_action == 'exit':
		playing = False
	#let mosnters take their turn
	if game_state == 'playing' and player_action != 'noturntaken' and player_action != 'exit':
		for object in objects:
			if object != player:
				print 'The ' + object.name + ' growls'
	pg.display.update()
	fpsClock.tick(LIMIT_FPS)