from tkinter import *
from Game_Leo import Game, Agent
from geometry import Point2D, Vector2D
import math
import random
import time
# WEDS, 11/29/17 AT 21:00 (LEO TOWNSEND)
# TO EASILY PICK COLORS: https://www.w3schools.com/colors/colors_picker.asp
TIME_STEP = 0.5

class MovingBody(Agent):

    def __init__(self, p0, v0, world):
        self.velocity = v0
        self.accel    = Vector2D(0.0,0.0)
        Agent.__init__(self,p0,world)

    def color(self):
        return "#000080"


    def shape(self):
        p1 = self.position + Vector2D( 0.125, 0.125)       
        p2 = self.position + Vector2D(-0.125, 0.125)        
        p3 = self.position + Vector2D(-0.125,-0.125)        
        p4 = self.position + Vector2D( 0.125,-0.125)
        return [p1,p2,p3,p4]

    def steer(self):
        return Vector2D(0.0)

    def update(self):
        self.position = self.position + self.velocity * TIME_STEP
        self.velocity = self.velocity + self.accel * TIME_STEP
        self.accel    = self.steer()
        self.world.trim(self)

class Shootable(MovingBody):

    SHRAPNEL_CLASS  = None
    SHRAPNEL_PIECES = 0
    WORTH           = 1

    def __init__(self, position0, velocity0, radius, world):
        self.radius = radius
        MovingBody.__init__(self, position0, velocity0, world)

    def is_hit_by(self, photon):
        return ((self.position - photon.position).magnitude() < self.radius)

    def explode(self):
        self.world.score += self.WORTH
        if self.SHRAPNEL_CLASS == None:
            return
        for _ in range(self.SHRAPNEL_PIECES):
            self.SHRAPNEL_CLASS(self.position,self.world)
        self.leave()

class Asteroid(Shootable):
    WORTH     = 5
    MIN_SPEED = 0.1
    MAX_SPEED = 0.3
    SIZE      = 3.0

    def __init__(self, position0, velocity0, world):
        Shootable.__init__(self,position0, velocity0, self.SIZE, world)
        self.make_shape()

    def choose_velocity(self):
        return Vector2D.random() * random.uniform(self.MIN_SPEED,self.MAX_SPEED) 
        
    def make_shape(self):
        angle = 0.0
        dA = 2.0 * math.pi / 15.0
        center = Point2D(0.0,0.0)
        self.polygon = []
        for i in range(15):
            if i % 3 == 0 and random.random() < 0.2:
                r = self.radius/2.0 + random.random() * 0.25
            else:
                r = self.radius - random.random() * 0.25
            dx = math.cos(angle)
            dy = math.sin(angle)
            angle += dA
            offset = Vector2D(dx,dy) * r
            self.polygon.append(offset)

    def shape(self):
        return [self.position + offset for offset in self.polygon]

class ParentAsteroid(Asteroid):
    def __init__(self,world):
        world.number_of_asteroids += 1
        velocity0 = self.choose_velocity()
        position0 = world.bounds.point_at(random.random(),random.random())
        if abs(velocity0.dx) >= abs(velocity0.dy):
            if velocity0.dx > 0.0:
                # LEFT SIDE
                position0.x = world.bounds.xmin
            else:
                # RIGHT SIDE
                position0.x = world.bounds.xmax
        else:
            if velocity0.dy > 0.0:
                # BOTTOM SIDE
                position0.y = world.bounds.ymin
            else:
                # TOP SIDE
                position0.y = world.bounds.ymax
        Asteroid.__init__(self,position0,velocity0,world)

    def explode(self):
        Asteroid.explode(self)
        self.world.number_of_asteroids -= 1

class Ember(MovingBody):
    INITIAL_SPEED = 2.0
    SLOWDOWN      = 0.2
    TOO_SLOW      = INITIAL_SPEED / 20.0

    def __init__(self, position0, world):
        velocity0 = Vector2D.random() * self.INITIAL_SPEED
        MovingBody.__init__(self, position0, velocity0, world)

    def color(self):
        white_hot  = "#FFFFFF"
        burning    = "#FF8080"
        smoldering = "#808040"
        speed = self.velocity.magnitude()
        if speed / self.INITIAL_SPEED > 0.5:
            return white_hot
        if speed / self.INITIAL_SPEED > 0.25:
            return burning
        return smoldering

    def steer(self):
        return -self.velocity.direction() * self.SLOWDOWN

    def update(self):
        MovingBody.update(self)
        if self.velocity.magnitude() < self.TOO_SLOW:
            self.leave()

class ShrapnelAsteroid(Asteroid):
    def __init__(self, position0, world):
        world.number_of_shrapnel += 1
        velocity0 = self.choose_velocity()
        Asteroid.__init__(self, position0, velocity0, world)

    def explode(self):
        Asteroid.explode(self)
        self.world.number_of_shrapnel -= 1

class SmallAsteroid(ShrapnelAsteroid):
    WORTH           = 20
    MIN_SPEED       = Asteroid.MIN_SPEED * 2.0
    MAX_SPEED       = Asteroid.MAX_SPEED * 2.0
    SIZE            = Asteroid.SIZE / 2.0
    SHRAPNEL_CLASS  = Ember
    SHRAPNEL_PIECES = 8

    def color(self):
        return "#634a33"

class MediumAsteroid(ShrapnelAsteroid):
    WORTH           = 10
    MIN_SPEED       = Asteroid.MIN_SPEED * math.sqrt(2.0)
    MAX_SPEED       = Asteroid.MAX_SPEED * math.sqrt(2.0)
    SIZE            = Asteroid.SIZE / math.sqrt(2.0)
    SHRAPNEL_CLASS  = SmallAsteroid
    SHRAPNEL_PIECES = 3

    def color(self):
        return "#7e5e40"

class LargeAsteroid(ParentAsteroid):
    SHRAPNEL_CLASS  = MediumAsteroid
    SHRAPNEL_PIECES = 2

    def color(self):
        return "#b0835a"

class Photon(MovingBody):
    INITIAL_SPEED = 2.0 * SmallAsteroid.MAX_SPEED
    LIFETIME      = 40
    # changing intial speed will result in a change of the range of your photon cannon
    # changing lifetime will change the range, but not the speed of the weapon

    def __init__(self,source,world):
        self.age  = 0
        v0 = source.velocity + (source.get_heading() * self.INITIAL_SPEED)
        MovingBody.__init__(self, source.position, v0, world)

    def color(self):
        return "#12ff03"

    def update(self):
        MovingBody.update(self)
        self.age += 1
        if self.age >= self.LIFETIME:
            self.leave()
        else:
            targets = [a for a in self.world.agents if isinstance(a,Shootable) and (not isinstance(a,Ship))]
            for t in targets:
                if(t.is_hit_by(self)):
                    t.explode()
                    self.leave()
                    return

# class Minable(Asteroid):


class Ship(Shootable):
    TURNS_IN_360   = 24
    IMPULSE_FRAMES = 4
    ACCELERATION   = 0.05
    MAX_SPEED      = 2.0
    
    #explode ship
    SHRAPNEL_CLASS  = Ember
    SHRAPNEL_PIECES = 50
    
    # die
    SIZE = 3.0
    DEATH_DELAY = 50
    SHIELD_UP = False
    SHIELD_TIMER = 250
    SHIELD_USES = 5
    ALIVE = True

    def __init__(self,world):
        position0    = Point2D()
        velocity0    = Vector2D(0.0,0.0)
        Shootable.__init__(self,position0,velocity0,self.SIZE,world)
        self.speed   = 0.0
        self.angle   = 90.0
        self.impulse = 0
        self.lives = 3
        self.recent_death = False
        self.death_delay = self.DEATH_DELAY # used in shield()
        self.shield_up = self.SHIELD_UP # used in shield()
        self.shield_timer = self.SHIELD_TIMER # used in shield()
        self.shield_uses = self.SHIELD_USES # used in shield()
        self.alive = self.ALIVE # used in shield()


    def color(self):
        if self.shield_up:
            return "#00FFFF" # cyan
            # return "#00F000" # bright green
        else:    
            # return "#F0C080" # tan?
            # return "#000000" # black
            # return "#FFFFFF" # white
            return "#a6b5b3" # light grey

            '''
            Google web color RGB
            "#_ _ _ _ _ _", each pair in order are R, G, B
             each _ is on a base 16 scale from 0-9,A-F from low to high red,
            green, or blue
            '''

    def get_heading(self):
        angle = self.angle * math.pi / 180.0
        return Vector2D(math.cos(angle), math.sin(angle))
        
    def turn_left(self):
        self.angle += 360.0 / self.TURNS_IN_360

    def turn_right(self):
        self.angle -= 360.0 / self.TURNS_IN_360

    def speed_up(self):
        self.impulse = self.IMPULSE_FRAMES

    def shoot(self):
        Photon(self, self.world)
    
    def shape(self):
        h  = self.get_heading()
        hp = h.perp()
        p1 = self.position + h * 2.0
        p2 = self.position + hp*0.3
        p3 = self.position + hp*0.7 - h*0.5
        p4 = self.position - h*0.2
        p5 = self.position - hp*0.7 - h*0.5
        p6 = self.position - hp*0.3
        return [p1,p2,p3,p4,p5,p6]

    def steer(self):
        if self.impulse > 0:
            self.impulse -= 1
            return self.get_heading() * self.ACCELERATION
        else:
            return Vector2D(0.0,0.0)

    def trim_physics(self):
        MovingBody.trim_physics(self)
        m = self.velocity.magnitude()
        if m > self.MAX_SPEED:
            self.velocity = self.velocity * (self.MAX_SPEED / m)
            self.impulse = 0

    def explode(self):
        if self.SHRAPNEL_CLASS == None:
            return
        for _ in range(self.SHRAPNEL_PIECES):
            self.SHRAPNEL_CLASS(self.position,self.world)
        # maybe explode could pause the asteroid movement and reboot the game with lives - 1 ?

    # maybe Ship should have its own leave method that inherits from leave, but changes life count
    def update(self):
        MovingBody.update(self)
        
        if self.shield_up:
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if ( (t is not self) and t.is_hit_by(self) ):
                    t.explode()
            print("update shield_up:",self.shield_up)
            print("update shield_timer:",self.shield_timer)

        elif self.recent_death == False and self.shield_up == False:
            # print("have not recently died")
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if ( (t is not self) and t.is_hit_by(self) ):
                    t.explode()
                    self.explode()
                    self.lives -= 1
                    self.recent_death = True
                    if self.lives >= 1:
                        self.death_delay = 150
                    else:
                        self.death_delay = 0
                        self.alive = False
                        self.world.GAME_OVER = True
                        print("Game over!")

                      # end of game
                      # some cool "GAME OVER" print screen would be nice
                        self.leave()
                        break
                
          # Needs to change GAME_OVER = True and say so
        elif self.recent_death == True and self.shield_up == False:
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if ( (t is not self) and t.is_hit_by(self) ):
                    # print("have died recently")
                    t.explode()
                    break

        if self.death_delay > 0:
            self.death_delay -= 1
        else:
            self.recent_death = False
            # death_delay gives the ship a moment of invincibility after striking an asteroid
#-------------------------------------------------------------------
        if self.shield_timer > 0:
            self.shield_timer -= 1
        else: # elif self.shield_timer == 0:
            # self.recent_death = False # shield_up = False
            self.shield_up = False
#-------------------------------------------------------------------
        # if self.shield_timer <= 250 and not self.shield_up:
        #     self.shield_timer += 1
                    # print to screen: number of lives
                    # need to pause game for a second and say DAMAGE SEVERE Lives = X
                    # reboot position, stop asteroid movement
                    # We could also destroy all small asteroids made by the impact, without subtracting lives?
    def shield(self): # <<<shield() IN PROGRESS>>>
        '''
        INSTRUCTIONS: "shields (2 points): Add a feature where a player can deploy 
        a shield, one that protects them from hitting obstacles (or being hit by them) 
        or from being attacked by antagonists. The shield should have a limited 
        lifetime. Also, there should be a limited number of uses available."

        HOW IT WORKS: If you are not already invulnerable from recent death, 
        pressing 's' will set self.shield_timer to some a value that decrements to 
        0. If shield runs out of power (hits 0), it will turn off and begin 
        regenerating.
        '''
        if not self.shield_up: 
            if self.shield_uses >= 1:
                print("shield_uses:", self.shield_uses)
                print("method shield_up:", self.shield_up)
                self.shield_up = True
                print("method shield_timer:", self.shield_timer)
                self.shield_timer = 250
                self.shield_uses -= 1
            else:
                print("No more shield uses!")

            # –– What is this shield method missing (aside from visual 
            # representation)?
            # –– Shield might also have a way to turn off using 's' again like 
            # pause/unpause but how?
            # –– Shield contact should hit other object.


# class Alien(Moving Body):

class PlayAsteroids(Game):

    DELAY_START      = 150
    MAX_ASTEROIDS    = 6
    INTRODUCE_CHANCE = 0.01
    
    def __init__(self):
        Game.__init__(self,"ASTEROIDS!!!",60.0,45.0,800,600,topology='wrapped')

        self.number_of_asteroids = 0
        self.number_of_shrapnel = 0
        self.level = 1
        self.score = 0

        self.before_start_ticks = self.DELAY_START
        self.started = False

        self.ship = Ship(self)

    def max_asteroids(self):
        return min(2 + self.level,self.MAX_ASTEROIDS)

    def handle_keypress(self,event):
        Game.handle_keypress(self,event)
        if event.char == 'i' or event.char == 'I':
            self.ship.speed_up()
        elif event.char == 'j' or event.char == 'J':
            self.ship.turn_left()
        elif event.char == 'l' or event.char == 'L':
            self.ship.turn_right()
        elif event.char == 'e' or event.char == 'E':
        # later on we may switch the cause of this event to an asteroid impact
        # Leo –– can maybe turn the explosion radius into an attack?
            self.ship.explode()
        elif event.char == ' ':
            if self.ship.alive == True:
                self.ship.shoot()
            else:
                print("You cannot shoot; you are dead.") #####
        elif event.char == 's' or event.char == 'S':
            print("'s' pressed.")
            self.ship.shield()
            # Above just calls shield() if 's' is pressed once; below will hopefully say: 
            # if 's' is pressed again before shield is depleted, shield will turn off
            # and start regenerating.
            '''
            if event.char == 's' and self.death_delay > 0:
                while self.death_delay <= 300:
                    self.death_delay += 1
            '''
        
    def update(self):

        # Are we waiting to toss asteroids out?
        if self.before_start_ticks > 0:
            self.before_start_ticks -= 1
        else:
            self.started = True
        
        # Should we toss a new asteroid out?
        if self.started:
            tense = (self.number_of_asteroids >= self.max_asteroids())
            tense = tense or (self.number_of_shrapnel >= 2*self.level)
            if not tense and random.random() < self.INTRODUCE_CHANCE:
                LargeAsteroid(self)

        Game.update(self)
        

print("Press 'j' and 'l' to turn, 's' to deploy a shield, 'i' to create thrust, and SPACE to shoot.")
print("Press 'q' to quit, and 'p' to pause.")
game = PlayAsteroids()
# can we add music to the game?  Some synthwave jams?
while not game.GAME_OVER:
    time.sleep(1.0/60.0)
    game.update()

# For minable asteroids: maybe decrement a counter till explosion. When you hit
# a minAst, increment a gem counter. Photons must know which of two types of Ast
# they hit (e.g. self.world.ship.gemcount += 1). // For dock, have to deal with
# 1) stopping ship movement, ship position controlled by dock, 2) when leaving
# dock, do not reattach immediately within a certain distance. // First, basics:
# 1) make a shield, a minableAst type, a pause option, 2) death, lives, dock

