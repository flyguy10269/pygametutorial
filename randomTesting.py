import random
import pygame as pg

pg.init()

blocksize = 50
blocks = 20

window = pg.display.set_mode((blocksize*blocks, blocksize*blocks))
screen = pg.display.get_surface()

colors = {
	'green':(0,205,0),
	'blue':(0,0,205),
	'red':(205,0,0)
	}
	
def blockolize():
	for x in range(blocks):
		for y in range(blocks):
			screen.fill(random.choice(colors.values()),
						pg.Rect( (x*blocksize, y*blocksize),
									(blocksize, blocksize) ))
									
blockolize()
pg.display.update()

playing = True
while playing:
	for event in pg.event.get():
		if event.type == pg.QUIT:
			playing = False
		elif event.type == pg.MOUSEBUTTONDOWN:
			blockolize()
			pg.display.update()