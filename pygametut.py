import random
import pygame as pg
from pygame.locals import *
import math
import textwrap
import shelve
import os

#import so pygame2exe functions correctly?
import pygame._view


pg.init()

PLAYER_IMAGE = os.path.join("data","images","snake.png")
CORPSE_IMAGE = os.path.join("data","images","corpse.png")
WALL_IMAGE = os.path.join("data","images","wall.png")
GRASS_IMAGE = os.path.join("data","images","grass.png")
TROLL_IMAGE = os.path.join("data","images","troll.png")
ORC_IMAGE = os.path.join("data","images","orc.png")
SLIME_IMAGE = os.path.join("data","images","slime.png")
SKELETON_IMAGE = os.path.join("data","images","skeleton.png")
HEALING_POTION_IMAGE = os.path.join("data","images","hp_potion.png")
LIGHTNING_SCROLL_IMAGE = os.path.join("data","images","lightning_scroll.png")
CONFUSE_SCROLL_IMAGE = os.path.join("data","images","confuse_scroll.png")
FIREBALL_SCROLL_IMAGE = os.path.join("data","images","fireball_scroll.png")


ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30
MAX_ROOM_MONSTERS=3
MAX_ROOM_ITEMS=2

fullscreen = False

#items
HP_POTION_AMOUNT = 5

#SCROLL OF LIGHTNING
LIGHTNING_DAMAGE=20
LIGHTNING_RANGE=5 

#SCROLL OF CONFUSION
CONFUSE_RANGE = 7
CONFUSED_NUM_TURNS = 10

#SCROLL OF FIREBALL
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12
FIREBALL_RANGE = 8

colors = {
			'green':(0,205,0),
			'blue':(0,0,205),
			'red':(205,0,0),
			'black':(0,0,0),
			'white':(205,205,205),
			'orange':(255,128,0),
			'pink':(255,0,255),
			'lightblue':(0,255,255),
			'grey':(128,128,128)
			}

BGCOLOR = colors['black']

#SCREEN SIZING
infoObject = pg.display.Info()


TILE_SIZE = 28
MAP_SIZE = infoObject.current_h/TILE_SIZE
map = []
LIMIT_FPS = 30
fpsClock = pg.time.Clock()

#side panel settings
panel = pg.Surface((500,(TILE_SIZE*MAP_SIZE)))
PANEL_X = TILE_SIZE*MAP_SIZE
PANEL_Y = 0
FONT_SIZE = 17
AntiA = True	#antialiasing
font = pg.font.Font(None, FONT_SIZE)

#message log settings
MSG_X = 5
MSG_Y = 600
MSG_HEIGHT = 8 #number of lines to display
MSG_WIDTH = 50 #number of characters for each line
game_msgs = []

#HP bar constants
HP_BAR_X = 50
HP_BAR_Y = 500


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
	def __init__(self, x, y, image,name, blocks=False, fighter=None, ai=None, item=None):
		self.x = x
		self.y = y
		self.image = image
		self.name = name
		self.blocks = blocks
		self.item = item
		if self.item:	#let the item component know who owns it
			self.item.owner = self

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

	def distance(self, x, y):
		#return the distance to some coordinates
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
		
	def send_to_back(self):
		#move object to be drawn first so other objects will display above
		global objects
		objects.remove(self)
		objects.insert(0,self)
		
	def draw(self):
		surfaceImage = pg.image.load(self.image).convert()
		window.blit(surfaceImage, (self.x*TILE_SIZE, self.y*TILE_SIZE))
	
	def clear(self):
		window.fill(BGCOLOR,pg.Rect((self.x,self.y),(TILE_SIZE,TILE_SIZE)))

class Item:
	def __init__(self, use_function=None):
		self.use_function = use_function

	def use(self):
		#call use_function if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner) #destroy after use, unless cancelled

	#an item that can be picked up and used
	def pick_up(self):
		#add to the player's inventory and remove from the map
		if len(inventory) >= 26:
			message('Your inventory is full, cannot pick up ' + self.owner.name + 
				'.', colors['lightblue'])
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('you picked up a ' + self.owner.name + '!',colors['green'])

	def drop(self):
		#add to the map and remove from player's inventory
		objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.x = player.x
		self.owner.y = player.y
		message('You dropped a '+self.owner.name+'.',colors['blue'])
		
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

	def heal(self, amount):
		#heal by the given amount without going over the maximum
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

	def attack(self, target):
		#a simple formula for attack damage
		damage = self.power - target.fighter.defense

		if damage > 0:
			#make the target take some damage
			message(self.owner.name + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points',
				colors['orange'])
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

class ConfusedMonster:
	def __init__(self, old_ai, num_turns=CONFUSED_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns
		
	def take_turn(self):
		if self.num_turns > 0: #still confused
			#move in a random direction
			self.owner.move(random.randint(-1,1),random.randint(-1,1))
			self.num_turns -= 1
			
		else:	#restore previous AI
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused',colors['blue'])

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
		x = random.randint(room.x1+1, room.x2-1)
		y = random.randint(room.y1+1, room.y2-1)

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

def place_items(room):
	num_items = random.randint(0,MAX_ROOM_ITEMS)
	for i in range(num_items):
		#choose a random spot for items
		x = random.randint(room.x1+1, room.x2-1)
		y = random.randint(room.y1+1, room.y2-1)

		#only place an item if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_percentage()
			if choice <30:
				#create a healing potion
				item_component = Item(use_function=cast_heal)
				item = Object(x,y,HEALING_POTION_IMAGE,'healing potion',item=item_component)
			
			elif choice <30+15:
				#create scroll of lightning
				item_component = Item(use_function=cast_lightning)
				item = Object(x,y,LIGHTNING_SCROLL_IMAGE,'scroll of lightning',item=item_component)
			
			elif choice <30+15+20:
				#create scroll of confusion
				item_component = Item(use_function=cast_confusion)
				item = Object(x,y,CONFUSE_SCROLL_IMAGE,'scroll of confusion',item=item_component)
				
#			elif choice <30+15+15+20:
				#create scroll of ice lance
				
			else:
				#create scroll of fireball
				item_component = Item(use_function=cast_fireball)
				item = Object(x,y,FIREBALL_SCROLL_IMAGE,'scroll of fireball',item=item_component)
				
				

			objects.append(item)
			item.send_to_back()	#items appear below other objects

def cast_heal():
	#heal the player
	if player.fighter.hp == player.fighter.max_hp:
		print('at full health')
		message('You are already at full health', colors['red'])
		return 'cancelled'

	message('Your wounds start to feel better!', colors['blue'])
	player.fighter.heal(HP_POTION_AMOUNT)

def cast_lightning():
	#find closest enemy
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None:	#no monster found within range
		message('no monster found within range')
		return 'cancelled'
		
	#zap it!
	message('A lightning bolt strikes the ' + monster.name + ' for ' + str(LIGHTNING_DAMAGE),colors['red'])
	monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confusion():
	#target monster
	message('Left-click to select, Right-click to cancel')
	monster = target_monster(CONFUSE_RANGE)
	if monster is None: return 'cancelled'

	#replace the monster's ai with a confused ai
	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster	#tell the new component who owns it
	message('The ' + monster.name + 'starts to stumble around',colors['blue'])

def cast_fireball():
	#ask the player for a target tile to throw fireball at
	message('Left-click a target tile or right-click to cancel.')
	(x,y) = target_tile(FIREBALL_RANGE)
	if x is None: return 'cancelled'
	message('The fireball explodes!',colors['red'])
	
	for obj in objects:	#damage every fighter within range, including player
		if obj.distance(x,y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned.')
			obj.fighter.take_damage(FIREBALL_DAMAGE)
			
def closest_monster(max_range):
		#find the closest monster to the player
		closest_enemy = None
		closest_dist = max_range + 1 #start with a slightly larger range
		
		for object in objects:
			if object.fighter and not object == player:
				#find the distance between selected object and the player
				dist = player.distance_to(object)
				if dist < closest_dist:	#closer than previous
					closest_enemy = object
					closest_dist = dist
		return closest_enemy

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
	print MAP_SIZE
	print "making map"
	global map, objects
	
	#the list of objects 
	objects = [player]
	
	map = [[Tile(True)
				for y in range(MAP_SIZE)]
					for x in range(MAP_SIZE)]
					
	rooms = []
	num_rooms = 0
	for r in range(MAX_ROOMS):
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
				place_items(new_room)
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
			#print('message redacted')

		#add the new line as a tuple, with the text and color
		game_msgs.append((line, color))

def msgbox(text, width=50):
	menu(250,2,text,[]) #use menu() as a sort of message box
	
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
	text = font.render(name + ': ' +str(value) + '/' + str(maximum),
		AntiA,colors['white'])
	panel.blit(text,(x+total_width/2,y))

def render_panel():
	#display message log
	y = 1
	for (line, color) in game_msgs:
		message = font.render(line,AntiA,color)
		panel.blit(message,(MSG_X,MSG_Y+(y*FONT_SIZE)))
		y+=1

	#draw name of object under the mouse
	under_object = font.render(get_names_under_mouse(),AntiA,colors['white'])
	panel.blit(under_object,(5,5))

def menu(x,y, header, options):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

	#calculate the height of the header after auto wrap and one line per option
	header_height = FONT_SIZE + 5
	height = len(options)*FONT_SIZE + header_height
	header = font.render(header,AntiA, colors['red'])
	window.blit(header,(x,y))
	#print all options
	y = header_height
	print x,y
	letter_index = ord('a')
	for option_text in options:
		text = font.render('(' + chr(letter_index) + ') ' + option_text,AntiA, colors['white'])
		window.blit(text,(x,y+(y*FONT_SIZE)))
		y+=1
		letter_index += 1

	#wait for a keypress
	selection = wait()

	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = selection - ord('a')
	if index >= 0 and index < len(options): 
		return index
		
	return None

def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = [item.name for item in inventory]
	index = menu(200,200,header, options)

	if index is None or len(inventory) == 0: return None
	return inventory[index].item

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
	render_panel()
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
		print 'unfullscreening'
		window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE))
		fullscreen = False

def wait():
	while True:
		for event in pg.event.get():
			if event.type == KEYDOWN:
				return event.key
		pg.display.update()

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
			elif event.key == K_g:
				#pick up an item
				for object in objects:	#look for an item in the players tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break
			elif event.key == K_i:
				#show inventory; if an item is selected, use it
				chosen_item = inventory_menu('Press the key next to an item to use it or any other key to cancel')
				if chosen_item is not None:
					#print('using ' + chosen_item.name)
					chosen_item.use()
			elif event.key == K_F8:
				cast_heal()
			elif event.key == K_d:
				#show the inventory; if an item is selected drop it
				chosen_item = inventory_menu('select item to be dropped')
				if chosen_item is not None:
					chosen_item.drop()
					
			#give item change for different item
			elif event.key == K_F9:
				item_component = Item(use_function=cast_fireball)
				item = Object(2,2,FIREBALL_SCROLL_IMAGE,'scroll of fireball',item=item_component)
				inventory.append(item)

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

def get_names_under_mouse():
	global mouse_pos
	mouse = pg.mouse.get_pos()

	#return a string with the names of all objects under the mouse
	(x,y) = (mouse)
	x = x/TILE_SIZE		#set mouse position to local coordinates
	y = y/TILE_SIZE

	names = [obj.name for obj in objects
		if obj.x == x and obj.y == y]

	names = ' , '.join(names)	#join the names, seperated by commas

	#display names by mouse cursor
	under_object = font.render(names.capitalize(),AntiA,colors['black'])
	window.blit(under_object,(mouse[0]+15,mouse[1]))

	return names.capitalize()	#capitalize first letter of names

def target_monster(max_range=None):
	#returns a clicked monster or None if right-clicked
	while True:
		(x,y) = target_tile(max_range)
		if x is None: #player cancelled
			return None
		#return the first clicked monster, otherwise continue loooping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj
				
def target_tile(max_range = None):
	global key
	while True:
		#render screen to erase inventory
		pg.display.update()
		render_all()
		
		for event in pg.event.get():
			if event.type == KEYDOWN and event.key == K_ESCAPE:
				message('action cancelled')
				return (None, None)
			if event.type == MOUSEBUTTONDOWN:
				(x,y) = pg.mouse.get_pos()
				x = x/TILE_SIZE
				y = y/TILE_SIZE

				if event.button == 1:
					if max_range is None or player.distance(x,y) <= max_range:
						return(x,y)
					else:
						message('Target out of range')
				if event.button == 3:
					message('action cancelled')
					return (None, None)

					
					
"""
new game and initializing and loading 
junk like that
"""
def new_game():
	global player, inventory, game_msgs, game_state

	
	#create player
	fighter_component = Fighter(hp=30,defense=2,power=50,death_function=player_death)
	player = Object(1,1,PLAYER_IMAGE,'player',blocks=True,fighter=fighter_component)
	
	#generate map 
	make_map()
	#initializeFOV()
	game_state = 'playing'
	inventory = []
	
	#create the list of game messages
	game_msgs = []
	
	#welcome message
	message('Welcome to the dungeon!',colors['red'])
	message('I hope you enjoy your stay.',colors['blue'])

#FUTURE FOV CALCULATION
#initializeFOV():

def play_game():
	global key, mouse, playing, wallSurface, grassSurface
	wallSurface = pg.image.load(WALL_IMAGE).convert()
	grassSurface = pg.image.load(GRASS_IMAGE).convert()
	
	#main surface window
	if fullscreen == True:
		window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE),pg.FULLSCREEN)
	else:
		window = pg.display.set_mode((TILE_SIZE*MAP_SIZE+500,TILE_SIZE*MAP_SIZE))
	player_action = None
	"""
	maybe not needed
	mouse = pg.mouse
	key = key nonsense
	"""
	
	pg.display.update()
	playing = True
	while playing:
		#render the screen
		window.fill(BGCOLOR)
		render_all()
		
		player_action = handle_keys()
		if player_action == 'exit':
			save_game()
			playing = False
		#let monsters take their turns
		if game_state == 'playing' and player_action != 'noturntaken' and player_action != 'exit':
			for object in objects:
				if object.ai:
					object.ai.take_turn()
		pg.display.update()
		fpsClock.tick(LIMIT_FPS)

def save_game():
	#open a new empty shelve overwritting an old one
	file = shelve.open('savegame', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player) #index of player in objects list
	file['inventory'] = inventory
	file['game_msgs'] = game_msgs
	file['game_state'] = game_state
	file.close()
	
def load_game():
	#open the previously saved shelve and load data
	global map, objects, player, inventory, game_msgs, game_state
	
	file = shelve.open('savegame', 'r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']] #get index of player in objects
	inventory = file['inventory']
	game_msgs = file['game_msgs']
	game_state = file['game_state']
	file.close()
	
def main_menu():
	global window
	window = pg.display.set_mode((600,500))
	bckgndSurface = pg.image.load(os.path.join("data","images","menu_background.png")).convert()
	window.blit(bckgndSurface,(0,0))
	while True:
		choice = menu(250,12,'main menu',['Play a new game',
											'Continue last game',
											'Quit'])
		if choice == 0: #new game
			new_game()
			play_game()
			
		elif choice == 1: #continue
			try:
				load_game()
			except:
				msgbox('\n No saved game to load.\n',24)
				continue
			play_game()
			
		elif choice == 2: #quit
			break


game_state = 'playing'
player_action = 'None'

main_menu()

"""	
EXAMPLES FROM TUTORIAL FOR THINGS TO CHANGE OR ADD
---------------AI--------------------------
ai to have a state system to know behaviours
class DragonAI:
	def __init__(self):
		self.state = 'chasing'
	def take_turn(self):
		if self.state == 'chasing': ...
		elif self.state == 'charging-fire-breath':...

-----------------------------------------------------
"""