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
CORPSE_IMAGE = os.path.join("data","images","corpse.png")
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
			'black':(0,0,0),
			'white':(205,205,205)
			}

BGCOLOR = colors['black']

#SCREEN SIZING
TILE_SIZE = 28
MAP_SIZE = 35
map = []
LIMIT_FPS = 30
fpsClock = pg.time.Clock()

#side panel settings
panel = pg.Surface((500,(TILE_SIZE*MAP_SIZE)))
PANEL_X = TILE_SIZE*MAP_SIZE
PANEL_Y = 0
FONT_SIZE = 17
AntiA = True	#antialiasing

#message log settings
MSG_X = 5
MSG_Y = 600
MSG_HEIGHT = 8 #number of lines to display
MSG_WIDTH = 50 #number of characters for each line
game_msgs = []

#HP bar constants
HP_BAR_X = 50
HP_BAR_Y = 500

#main surface window
window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE))
#GUI side panel
panel = pg.Surface((500,(TILE_SIZE*MAP_SIZE)))


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
	def __init__(self, x, y, image,name, blocks=False, fighter=None, ai=None):
		self.x = x
		self.y = y
		self.image = image
		self.surfaceImage = pg.image.load(image).convert()
		self.name = name
		self.blocks = blocks

		self.fighter = fighter
		if self.fighter: #let the fighter component know who owns it
			self.fighter.owner = self
		self.ai = ai
		if self.ai: #let the AI component know who owns it
			self.ai.owner = self

	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def move_towards(self,target_x,target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)

		#normalize it to length 1 (preserving direction), then round it and
		#convert to integer so the movement is restricted to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy **2)

	def send_to_back(self):
		#move object to be drawn first so other objects will display above
		global objects
		objects.remove(self)
		objects.insert(0,self)
		
	def draw(self):
		window.blit(self.surfaceImage, (self.x*TILE_SIZE, self.y*TILE_SIZE))
	
	def clear(self):
		window.fill(BGCOLOR,pg.Rect((self.x,self.y),(TILE_SIZE,TILE_SIZE)))

class Fighter():
	#combat related properties and methods
	def __init__(self, hp, defense, power,death_function=None):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.death_function = death_function

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				function(self.owner)

	def attack(self, target):
		#a simple formula for attack damage
		damage = self.power - target.fighter.defense

		if damage > 0:
			#make the target take some damage
			message(self.owner.name + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points',
				colors['red'])
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name + ' attacks ' + target.name + ' but it has no effect',colors['blue'])

class BasicMonster:
	#AI for a basic monster
	def take_turn(self):
		#a basic monster takes its turn.
		monster = self.owner
		distance_to_player = monster.distance_to(player)
		if distance_to_player >=2 and distance_to_player <10:
			monster.move_towards(player.x, player.y)

		#close enough to attack
		elif player.fighter.hp > 0 and distance_to_player <2:
			monster.fighter.attack(player)

def player_death(player):
	#the game ended
	global game_state
	message('You have died!',colors['red'])
	print 'You died'
	game_state = 'dead'

	#for added effect transform player into a corpse
	player.image = CORPSE_IMAGE

def monster_death(monster):
	#transform it into a corpse that doesn't block movement
	message(monster.name + ' is dead.')
	monster.image = CORPSE_IMAGE
	monster.surfaceImage = pg.image.load(CORPSE_IMAGE).convert()
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()

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
				fighter_component = Fighter(hp=10,defense=0,power=3,death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x,y,ORC_IMAGE,"orc",blocks=True,
					fighter = fighter_component,ai=ai_component)
			elif choice <10+30:
				#create a troll 30% chance
				fighter_component = Fighter(hp=10,defense=0,power=2,death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x,y,TROLL_IMAGE,"troll",blocks=True,
					fighter = fighter_component,ai=ai_component)
			elif choice < 10+30+10:
				#create skeleton 10% chance
				fighter_component = Fighter(hp=10,defense=0,power=1,death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x,y,SKELETON_IMAGE,"skeleton",blocks=True,
					fighter=fighter_component,ai=ai_component)
			else:
				#create slime 50% chance
				fighter_component = Fighter(hp=3,defense=0,power=1,death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x,y,SLIME_IMAGE,"slime",blocks=True,
					fighter=fighter_component,ai=ai_component)
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
			if new_room.intersect(other_room):
				failed = True
				break
				
		if not failed:
			
			create_room(new_room)
			(new_x, new_y) = new_room.center()
			if num_rooms == 0:
				print "first room created"
				player.x = new_x
				player.y = new_y
			
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
		if object.fighter and object.x == x and object.y == y:
			target = object
			break

	#attack if target found, move otherwise
	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)	
	
def message(new_msg, color = colors['white']):
	#split the message if needed
	new_msg_lines = textwrap.wrap(new_msg,MSG_WIDTH)

	for line in new_msg_lines:
		#if the buffer is full, remove the first line
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]
			print('message redacted')

		#add the new line as a tuple, with the text and color
		game_msgs.append((line, color))

def render_bar(x,y,total_width,name,value,maximum,bar_color,back_color):
	#clear side panel
	panel.fill(colors['black'])
	#render a bar (hp, experience, etc). first calculation the width of the bar
	bar_width = int(float(value) / maximum * total_width)

	#render the bar on top
	bar = panel.subsurface(pg.Rect((x,y),(bar_width,20)))

	#testing bar
	bar.fill(bar_color)
	window.blit(panel,(TILE_SIZE*MAP_SIZE,300))

	#text with values
	font = pg.font.Font(None, FONT_SIZE)
	text = font.render(name + ': ' +str(value) + '/' + str(maximum),
		AntiA,colors['white'])

	panel.blit(text,(x+total_width/2,y))

	#display messages
	y = 1
	for (line, color) in game_msgs:
		message = font.render(line,AntiA,color)
		panel.blit(message,(MSG_X,MSG_Y+(y*FONT_SIZE)))
		y += 1


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
		if object != player:
			object.draw()
		player.draw()

	render_bar(HP_BAR_X,HP_BAR_Y,300,'HP',player.fighter.hp,player.fighter.max_hp,
			colors['red'],colors['black'])
	window.blit(panel,(PANEL_X,PANEL_Y))

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
			elif event.key == K_F7:
				player.fighter.take_damage(7)
				message('You deal 7 damage to yourself')

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

fighter_component = Fighter(hp=30,defense=2,power=50,death_function=player_death)
player = Object(1,1,PLAYER_IMAGE,'player',blocks=True,fighter=fighter_component)
objects = [player]

make_map()
wallSurface = pg.image.load(WALL_IMAGE).convert()
grassSurface = pg.image.load(GRASS_IMAGE).convert()

pg.display.update()
playing = True

game_state = 'playing'
player_action = 'None'

#test messaging
message('Welcome to the dungeon!',colors['red'])
message('I hope you enjoy your stay.',colors['blue'])


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
			if object.ai:
				object.ai.take_turn()
	pg.display.update()
	fpsClock.tick(LIMIT_FPS)