
#! /usr/bin/env python3

"""Flappy Bird, implemented using Pygame."""

import math
import os
import ast,copy,re
import random
from random import randint
from collections import deque

import pygame
from pygame.locals import *
f=0
c=1
dict={}
FPS = 60
ANIMATION_SPEED = 0.18  # pixels per millisecond
WIN_WIDTH = 284 * 2     # BG image size: 284x512 px; tiled twice
WIN_HEIGHT = 512
max_score=0
random_pipe=[4,3,1,2,4,6,2]
class Node:
    def __init__(self,state,count_up,count_down,Action_up=[],Action_down=[]):
        self.state = state
        self.count_up = count_up
        self.count_down = count_down
        self.Action_down = Action_down
        self.Action_up = Action_up
     

class Bird(pygame.sprite.Sprite):
    """Represents the bird controlled by the player.
    The bird is the 'hero' of this game.  The player can make it climb
    (ascend quickly), otherwise it sinks (descends more slowly).  It must
    pass through the space in between pipes (for every pipe passed, one
    point is scored); if it crashes into a pipe, the game ends.
    Attributes:
    x: The bird's X coordinate.
    y: The bird's Y coordinate.
    msec_to_climb: The number of milliseconds left to climb, where a
        complete climb lasts Bird.CLIMB_DURATION milliseconds.
    Constants:
    WIDTH: The width, in pixels, of the bird's image.
    HEIGHT: The height, in pixels, of the bird's image.
    SINK_SPEED: With which speed, in pixels per millisecond, the bird
        descends in one second while not climbing.
    CLIMB_SPEED: With which speed, in pixels per millisecond, the bird
        ascends in one second while climbing, on average.  See also the
        Bird.update docstring.
    CLIMB_DURATION: The number of milliseconds it takes the bird to
        execute a complete climb.
    """

    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.18
    CLIMB_SPEED = 0.3
    CLIMB_DURATION = 333.3

    def __init__(self, x, y, msec_to_climb, images):
        """Initialise a new Bird instance.
        Arguments:
        x: The bird's initial X coordinate.
        y: The bird's initial Y coordinate.
        msec_to_climb: The number of milliseconds left to climb, where a
            complete climb lasts Bird.CLIMB_DURATION milliseconds.  Use
            this if you want the bird to make a (small?) climb at the
            very beginning of the game.
        images: A tuple containing the images used by this bird.  It
            must contain the following images, in the following order:
                0. image of the bird with its wing pointing upward
                1. image of the bird with its wing pointing downward
        """
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
        """Update the bird's position.
        This function uses the cosine function to achieve a smooth climb:
        In the first and last few frames, the bird climbs very little, in the
        middle of the climb, it climbs a lot.
        One complete climb lasts CLIMB_DURATION milliseconds, during which
        the bird ascends with an average speed of CLIMB_SPEED px/ms.
        This Bird's msec_to_climb attribute will automatically be
        decreased accordingly if it was > 0 when this method was called.
        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.CLIMB_DURATION
            self.y -= (Bird.CLIMB_SPEED * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self):
        """Get a Surface containing this bird's image.
        This will decide whether to return an image where the bird's
        visible wing is pointing upward or where it is pointing downward
        based on pygame.time.get_ticks().  This will animate the flapping
        bird, even though pygame doesn't support animated GIFs.
        """
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):
        """Get a bitmask for use in collision detection.
        The bitmask excludes all pixels in self.image with a
        transparency greater than 127."""
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):
        """Get the bird's position, width, and height, as a pygame.Rect."""
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    """Represents an obstacle.
    A PipePair has a top and a bottom pipe, and only between them can
    the bird pass -- if it collides with either part, the game is over.
    Attributes:
    x: The PipePair's X position.  This is a float, to make movement
        smoother.  Note that there is no y attribute, as it will only
        ever be 0.
    image: A pygame.Surface which can be blitted to the display surface
        to display the PipePair.
    mask: A bitmask which excludes all pixels in self.image with a
        transparency greater than 127.  This can be used for collision
        detection.
    top_pieces: The number of pieces, including the end piece, in the
        top pipe.
    bottom_pieces: The number of pieces, including the end piece, in
        the bottom pipe.
    Constants:
    WIDTH: The width, in pixels, of a pipe piece.  Because a pipe is
        only one piece wide, this is also the width of a PipePair's
        image.
    PIECE_HEIGHT: The height, in pixels, of a pipe piece.
    ADD_INTERVAL: The interval, in milliseconds, in between adding new
        pipes.
    """

    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000
    
    
    def __init__(self, pipe_end_img, pipe_body_img):
        """Initialises a new random PipePair.
        The new PipePair will automatically be assigned an x attribute of
        float(WIN_WIDTH - 1).
        Arguments:
        pipe_end_img: The image to use to represent a pipe's end piece.
        pipe_body_img: The image to use to represent one horizontal slice
            of a pipe's body.
        """
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()   # speeds up blitting
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -                  # fill window from top to bottom
             3 * Bird.HEIGHT -             # make room for bird to fit through
             3 * PipePair.PIECE_HEIGHT) /  # 2 end pieces + 1 body piece
            PipePair.PIECE_HEIGHT)          # to get number of pipe pieces
        if c==7:
            c=0
        self.bottom_pieces = randint(1,total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces
        global c
        c+=1

        # bottom pipe
        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # top pipe
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        # compensate for added end pieces
        self.top_pieces += 1
        self.bottom_pieces += 1

        # for collision detection
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        """Get the top pipe's height, in pixels."""
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        """Get the bottom pipe's height, in pixels."""
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        """Get whether this PipePair on screen, visible to the player."""
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self):
        """Get the Rect which contains this PipePair."""
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
        """Update the PipePair's position.
        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        """Get whether the bird collides with a pipe in this PipePair.
        Arguments:
        bird: The Bird which should be tested for collision with this
            PipePair.
        """
        return pygame.sprite.collide_mask(self, bird)


def load_images():
    """Load all images required by the game and return a dict of them.
    The returned dict has the following keys:
    background: The game's background image.
    bird-wingup: An image of the bird with its wing pointing upward.
        Use this and bird-wingdown to create a flapping bird.
    bird-wingdown: An image of the bird with its wing pointing downward.
        Use this and bird-wingup to create a flapping bird.
    pipe-end: An image of a pipe's end piece (the slightly wider bit).
        Use this and pipe-body to make pipes.
    pipe-body: An image of a slice of a pipe's body.  Use this and
        pipe-body to make pipes.
    """

    def load_image(img_file_name):
        """Return the loaded pygame image with the specified file name.
        This function looks for images in the game's images folder
        (./images/).  All images are converted before being returned to
        speed up blitting.
        Arguments:
        img_file_name: The file name (including its extension, e.g.
            '.png') of the required image, without a file path.
        """
        file_name = os.path.join('.', 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img

    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            # images for animating the flapping bird -- animated GIFs are
            # not supported in pygame
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):
    """Convert frames to milliseconds at the specified framerate.
    Arguments:
    frames: How many frames to convert to milliseconds.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):
    """Convert milliseconds to frames at the specified framerate.
    Arguments:
    milliseconds: How many milliseconds to convert to frames.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return fps * milliseconds / 1000.0
def getState (bird,pp):
    x = int(pp.x) - int(bird.x)
    #print "------ x",x, "bottom", pp.PIECE_HEIGHT
    y = abs(int(pp.PIECE_HEIGHT*4) - int(bird.y))
    
    return (x,y)
def printToFile():
    f = open('complete_random.txt','w')
    for k,v in dict.iteritems():
        f.write(str(v.state))
        f.write("\n")
        f.write(str(v.Action_up))
        f.write("\n")
        f.write(str(v.Action_down))
        f.write("\n")
    
    #f.write('hi there\n') 
    f.close() 
def readFromFile():
    f=open("complete_random.txt")
    while True:
        
        nl=f.readline()
        if nl=="":
            break
        
        nl=nl.replace("(","")
        nl=nl.replace(")","")
        nl=nl.split(",")
        node = Node((int(nl[0]),int(nl[1])),1,1,Action_down=[],Action_up=[])
        dict[(int(nl[0]),int(nl[1]))]=node
        
        #print node.state
        nl=f.readline()
        if nl=="":
            break
        temp_up= ast.literal_eval(nl)
        node.Action_up=copy.deepcopy(temp_up)
        #print node.Action_up
        nl=f.readline()
        if nl=="":
            break
        temp_down= ast.literal_eval(nl)
        node.Action_down=copy.deepcopy(temp_down)
        #print node.Action_down
        #print"--------------------------"
def get_reward(curr_action,node):
    if curr_action=="up":
        if node.count_up>8:
            return -2000
        else:
            return -1000 
    else:
        if node.count_down>8:
            return -2000
        else:
            return -1000    
def main():
    """The application's entry point.
    If someone executes this module (instead of importing it, for
    example), this function is called.
    """
    
    flag=False
    
    gamma=0.95
    pygame.init()

    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Pygame Flappy Bird')

    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)  # default font
    images = load_images()

    # the bird stays in the same x position, so bird.x is a constant
    # center bird on screen
    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()
    new_node=""
    frame_clock = 0  # this counter is only incremented if the game isn't paused
    score = 0
    done = paused = False
    t=0
    global c
    c=1
    curr_flag= True
    while not done:
        #print "---------------------------------------------max_score---------",max_score
        reward = 0
        flag_dead=False
        clock.tick(FPS)
        #bird.msec_to_climb = Bird.CLIMB_DURATION
        # Handle this 'manually'.  If we used pygame.time.set_timer(),
        # pipe addition would be messed up when paused.
        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pp = PipePair(images['pipe-end'], images['pipe-body'])
            pipes.append(pp)
       # print "frame clock---->",frame_clock,curr_flag,flag
        if frame_clock%10==0 and curr_flag:                  #-------current state loop-----------------------
            current_state = getState(bird,pp)
            #print "current state",current_state
            if not dict.has_key(current_state):
                curr_node=Node(current_state,1,1,Action_down=[0],Action_up=[0])
                dict[current_state]=curr_node
            else :
                #print "node was present"
                curr_node = dict[current_state]
            #-----------------next Action-------------------
            
            if(len(curr_node.Action_up)>=t+1):
                ca=curr_node.Action_up[t]
            else:
                ca=curr_node.Action_up[-1]
            if(len(curr_node.Action_down)>=t+1):
                cb=curr_node.Action_down[t]
            else:
                 cb=curr_node.Action_down[-1]
            
           
           
            if(ca>cb):
            #if(randint(0,1)==1):
                bird.msec_to_climb = Bird.CLIMB_DURATION
                curr_action="up"
                curr_node.count_up=curr_node.count_up+1
            else:
                curr_action="down" 
                curr_node.count_down=curr_node.count_down+1
            #print "------current action up is",ca
            #print "------current action down is",cb
            #print"\n" 
            flag = True
            curr_flag=False
            
        
        
        for e in pygame.event.get():
            #
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
                printToFile()
            if e.type == MOUSEBUTTONUP or (e.type == KEYUP and e.key in (K_UP, K_RETURN, K_SPACE)):
                break

            '''if (flag) in (1,2,6,7,9,12,15,16,19,10):            
                bird.msec_to_climb = Bird.CLIMB_DURATION
                #flag=flag+1
                #break
            #bird.msec_to_climb = Bird.CLIMB_DURATION
            flag=flag+1;
            print flag'''
        
        if paused:
            continue  # don't draw anything

        # check for collisions
        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
          
            reward=get_reward(curr_action,curr_node)
            #print "--------------------------------------------dead--------------------------------------"
            done = True
            flag_dead=False
            #print "curr state is", curr_node.state, "new_state", new_node.state
            if curr_action=="up":
                expected_q=new_node.Action_up[-1]
                temp =(reward+gamma*(expected_q-ca))
                #alpha = (float(1)/float(curr_node.count_up))
                q = ca + temp*alpha
                q=round(q,2)
                curr_node.Action_up.append(q)
                #print 'new q is',q,"for ",curr_node.state
            else:
                expected_q=new_node.Action_down[-1]
                temp =(reward+gamma*(expected_q-cb))
                #alpha = (float(1)/float(curr_node.count_down))
                q = cb + temp*alpha
                q=round(q,2)
                curr_node.Action_down.append(q)
                #print 'new q is',q,"for ",curr_node.state, curr_node.Action_down[-1]
                
                
            
        else:
            reward = 0

        for x in (0, WIN_WIDTH / 2):
            display_surface.blit(images['background'], (x, 0))

        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        bird.update()
        display_surface.blit(bird.image, bird.rect)

        # update and display score
        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True
                reward=reward+5
                

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))
        score_surface1 = score_font.render(str(max_score), True, (255, 255, 255))
        score_x1 = WIN_WIDTH/2.5 - score_surface.get_width()/2.5
        display_surface.blit(score_surface1, (score_x1, PipePair.PIECE_HEIGHT))
        score_surface2 = score_font.render("Max", True, (255, 255, 255))
        score_x2 = WIN_WIDTH/4 - score_surface.get_width()/4
        display_surface.blit(score_surface2, (score_x2, PipePair.PIECE_HEIGHT))

        pygame.display.flip()
        frame_clock += 1
       # print "frame clock---->",frame_clock,curr_flag,flag
        if flag and frame_clock%10==0:
            flag=False
            curr_flag=True
            if (flag_dead):
                flag_dead=False
                reward=get_reward(curr_action,curr_node)
            new_state=getState(bird,pp)
            #print "new state",new_state
            if not dict.has_key(new_state):
                new_node=Node(new_state,1,1,Action_down=[0],Action_up=[0])
                dict[new_state]=new_node
            else :
                new_node=dict[new_state]
            if(len(new_node.Action_up)>=t+1):
                a=new_node.Action_up[t]
            else:
                a=new_node.Action_up[-1]
            if(len(new_node.Action_down)>=t+1):
                b=new_node.Action_down[t]
            else:
                b=new_node.Action_down[-1]
            if (a>b):        
                expected_q = a
               # print "expected q is",a,"for ",new_state
            else:
                expected_q = b
                #print "expected q is",b,"for ",new_state
            if curr_action=="up":
                #print "reward : ",reward
                temp=(reward+gamma*(expected_q-ca))
                #print "temp :",temp
                alpha = (float(1)/float(curr_node.count_up))
                #print "alpha ***up:",alpha
                #print temp*alpha
                
                q = ca + temp*alpha
                q=round(q,2)
                curr_node.Action_up.insert(t,q)
                #print 'new q is',q,"for ",curr_node.state
            else:
                #print "reward : ",reward
                temp=(reward+gamma*(expected_q-cb))
                #print "temp :",temp
                #print "curr node count down",curr_node.count_down
                
                alpha = (float(1)/float(curr_node.count_down))
                #print "alpha *** down :",alpha
                #print temp*alpha
                q = cb + temp*alpha
                q=round(q,2)
                curr_node.Action_down.insert(t,q)
                #print 'new q is',q,"for ",curr_node.state
            t=t+1
        global max_score
        if (score>max_score):
            max_score=score
        
        global f
        f=f+1
        if f==300000:
            printToFile()
    #print "\n" 
    
    print('Game over! Score: %i' % score)
   # pygame.quit()


if __name__ == '__main__':
    # If this module had been imported, __name__ would be 'flappybird'.
    # It was executed (e.g. by double-clicking the file), so call main.
    readFromFile()
    while f<300000:
	    
		main()
        
        
