"""A five-minute Cairo scene. All times are seconds on the recording timeline."""
from functools import lru_cache
import json
import math
import os
from pathlib import Path

import numpy as np
from manim import (
    Scene, VGroup, RoundedRectangle, DashedLine, VMobject, Text, MathTex, Line, Polygon, Circle, Dot,
    UpdateFromAlphaFunc, config, linear, LEFT,
)

ROOT = Path(__file__).resolve().parents[1]
BG, WHITE, MUTED = "#101722", "#F4F1E8", "#A8B6C7"
GOLD, TEAL, CORAL = "#FFD166", "#56D7BE", "#FF887D"
GRID, DASH = "#293747", "#5E7789"
config.background_color = BG


def point(x, y):
    return np.array([x, y, 0.])


def ramp(time, start, end):
    u = np.clip((time-start)/(end-start), 0., 1.)
    return u*u*(3-2*u)


@lru_cache(maxsize=512)
def letter(value, size, color, bold):
    return Text(value, font="Arial", font_size=size, color=color,
                weight="BOLD" if bold else "NORMAL", disable_ligatures=True)


@lru_cache(maxsize=150)
def formula(tex, size, color):
    return MathTex(tex, font_size=size, color=color)


def label(value, x, y, size=23, color=WHITE, bold=False, width=None, center=False):
    m = letter(value, size, color, bold).copy()
    if width and m.width > width:
        m.scale_to_fit_width(width)
    m.move_to(point(x, y))
    if not center:
        m.shift(point(m.width/2, 0))
    return m


def math_at(tex, x, y, size=35, color=WHITE, width=4.48):
    m = formula(tex, size, color).copy()
    if m.width > width:
        m.scale_to_fit_width(width)
    return m.move_to(point(x, y), aligned_edge=LEFT)


def segment(a, b, color, width=2):
    return Line(a, b, color=color, stroke_width=width)


def arrow(a, b, color, width=4, head=.13):
    delta = b-a
    length = np.linalg.norm(delta)
    if length < .003:
        return VGroup()
    d = delta/length
    ortho = point(-d[1], d[0])
    h = min(head, length*.45)
    base = b-h*d
    return VGroup(segment(a, base+.025*h*d, color, width),
                  Polygon(b, base+.45*h*ortho, base-.45*h*ortho,
                          stroke_width=0, fill_color=color, fill_opacity=1))


U=np.array([3.,1.])
V=np.array([-1.,2.])
ZERO=np.zeros(2)
GOAL=U+V
ORIGIN=point(-3.72,-.84)
UNIT=.76

def floor(p):
    return ORIGIN+UNIT*point(*p)

@lru_cache(maxsize=1)
def drafting_grid():
    g=VGroup()
    for x in range(-3,7):
        g.add(segment(floor((x,-2.6)),floor((x,4.05)),GRID,1.4))
        if x:g.add(label(str(x).replace("-","−"),*floor((x,-.27))[:2],16,MUTED,center=True))
    for y in range(-2,5):
        g.add(segment(floor((-3.87,y)),floor((6.75,y)),GRID,1.4))
        if y:g.add(label(str(y).replace("-","−"),*floor((-.28,y))[:2],16,MUTED,center=True))
    g.add(arrow(floor((-3.87,0)),floor((6.75,0)),DASH,2,.11),
          arrow(floor((0,-2.6)),floor((0,4.05)),DASH,2,.11))
    g.add(label("x",*floor((6.48,.23))[:2],18,MUTED),
          label("y",*floor((.17,3.87))[:2],18,MUTED))
    return g

@lru_cache(maxsize=1)
def chassis():
    body=RoundedRectangle(width=.36,height=.25,corner_radius=.055,fill_color="#27394B",
                          fill_opacity=1,stroke_color=WHITE,stroke_width=2.2)
    wheels=VGroup(*[RoundedRectangle(width=.21,height=.075,corner_radius=.026,
            fill_color=MUTED,fill_opacity=1,stroke_width=0).shift(point(0,y)) for y in (-.146,.146)])
    nose=segment(point(.12,-.055),point(.12,.055),TEAL,2.8)
    return VGroup(wheels,body,nose,Dot(radius=.042,color=WHITE))

def robot(position,heading=U):
    return chassis().copy().rotate(math.atan2(heading[1],heading[0])).move_to(floor(position))

def move_arrow(tail,displacement,color,width=5):
    return arrow(floor(tail),floor(tail+displacement),color,width,.17)

def scalar(s):
    return (1-.5*ramp(s,200,202)-.5*ramp(s,213,215)-ramp(s,219,221)
            +3*ramp(s,230,233)-1.5*ramp(s,247,249))

def num(x):
    return f"{x:.2f}".rstrip("0").rstrip(".").replace("-","−") if abs(x)>.0049 else "0"

MOVES=[(8,11),(13,16),(35,38),(39,41),(80,82),(84,86),(89,91),(92,94),
       (98,100),(120,122),(125,127),(133,135),(140,143),(146,149),(158,161),
       (200,202),(213,215),(219,221),(230,233),(247,249),(251,253),(255,257),(269,272)]
CUTS=[0,6,18,30,34,43,52,62,70,75,78,88,96,101,106,111,117,123,129,137,151,
      156,164,169,174,180,187,190,196,205,217,225,235,240,246,250,254,258,260,266,
      274,279,283,286,300]
TITLES=["What Is a Vector?","Three views of one move","Read the change","Put the moves together",
        "Scale the first command","One command to the ring"]

class Vectors(Scene):
    def get_moving_and_static_mobjects(self,animations):
        return list(self.mobjects),[]

    def construct(self):
        self.person=json.loads((ROOT/"project.json").read_text())
        self.canvas=VGroup()
        self.add(self.canvas)
        clips=[(96,102),(131,137),(211,223)] if os.getenv("VECTORS_CLIP")=="motion" else [(0,300)]
        for lo,hi in clips:
            times=sorted({lo,hi}|{t for t in CUTS+[t for pair in MOVES for t in pair] if lo<t<hi})
            for a,b in zip(times,times[1:]):
                self.paint(a)
                if any(l<=a<b<=r for l,r in MOVES):
                    self.play(UpdateFromAlphaFunc(self.canvas,lambda _,u:self.paint(a+(b-a)*u),
                                                  rate_func=linear),run_time=b-a,rate_func=linear)
                else:self.wait(b-a,frozen_frame=True)

    def paint(self,s):
        scene=sum(s>=t for t in (30,75,120,190,260))
        nodes=[drafting_grid()]
        add=nodes.append
        def side(words,y,size=23,c=WHITE):add(label(words,1.98,y,size,c,width=4.72))
        def eq(tex,y,c=WHITE):add(math_at(tex,1.98,y,37,c,4.65))
        def tag(words,p,dx,dy,c):
            x,y=floor(p)[:2]
            add(label(words,x+dx,y+dy,21,c,True))
        def vector(tail,d,c,name=None,offset=(.12,.18)):
            add(move_arrow(tail,d,c))
            if name:tag(name,tail+d,*offset,c)
        def trail(a,b,c):
            if np.linalg.norm(a-b)>.001:add(segment(floor(a),floor(b),c,2.6))
        def guide(a,b,c):
            if np.linalg.norm(np.array(a)-b)>.01:
                add(DashedLine(floor(a),floor(b),dash_length=.085,color=c,stroke_width=2.2))
        def ring(p):
            add(Circle(radius=.23,color=GOLD,stroke_width=2.5).move_to(floor(p)))
        def bent(u,v):
            pos=u*U+v*V
            trail(ZERO,u*U,"#6C978E")
            trail(u*U,pos,"#AE847F")
            return pos
        add(label("M3    /    LINEAR ALGEBRA",-6.61,3.60,16,TEAL,True))
        add(label(TITLES[scene],-6.63,3.03,36,WHITE,True,width=8.10))
        add(segment(point(1.66,-3.47),point(1.66,3.05),GRID,1.5))
        add(label(f"0{scene+1}   /   06",5.77,3.60,16,MUTED))
        add(segment(point(-6.61,-3.06),point(1.38,-3.06),GRID,1.4))
        footer=["Robot centre  ·  tracked point","Command 01  ·  displacement","Solid arrow  /  dashed component guides",
                "World axes  ·  right and up are positive","Base command  ·  u = (3, 1)","Goal ring  ·  (2, 3)"][scene]
        add(label(footer,-6.62,-3.39,20,MUTED))
        if scene==0:
            u,v=ramp(s,8,11),ramp(s,13,16)
            pos=bent(u,v)
            if s>=16:ring(GOAL)
            add(robot(pos,U if s<13 else V))
            side("One Robot, Two Numbers,",2.25,28)
            side("One Arrow",1.72,28)
            side("Linear combinations of vectors",1.07,20,TEAL)
            if s<18:
                side(self.person["STUDENT_NAME"],-.04)
                side(self.person["STUDENT_ID"],-.55,20,MUTED)
            else:
                side("Can one command",-.25,26,GOLD)
                side("reach the same ring?",-.82,26,GOLD)
        elif scene==1:
            u=ramp(s,35,38)
            pos=u*U
            trail(ZERO,pos,TEAL)
            if s>=39:
                vector(ZERO,U*ramp(s,39,41),TEAL)
            if s>=41:tag("u",U,.14,.21,TEAL)
            add(robot(pos))
            side("Controller",2.36,22,TEAL)
            eq(r"u=(3,1)",1.73)
            if s>=43:
                side("Floor",.98,22,TEAL)
                side("Length and direction",.49)
            if s>=52:
                side("Linear algebra",-.22,22,TEAL)
                side("Add vectors · scale vectors",-.74)
            if 62<=s<70:
                side("Inventory", -1.52,20,CORAL)
                side("[wheels, sensors] = [4, 2]",-2.05,22)
            if s>=70:side("Back on the floor  →  (3, 1)",-1.87,22)
        elif scene==2:
            vector(ZERO,U,TEAL,"u")
            if s>=80:
                guide(ZERO,(3*ramp(s,80,82),0),MUTED)
                tag("3",(1.5,0),-.08,-.53,TEAL)
            if s>=84:
                guide((3,0),(3,ramp(s,84,86)),MUTED)
                tag("1",(3,.47),.19,0,CORAL)
            side("Horizontal, then vertical",2.36,25)
            if s>=88:
                eq("u=",1.31)
                for x,sign in ((2.97,1),(3.96,-1)):
                    add(segment(point(x,.80),point(x,1.82),WHITE))
                    for y in (.80,1.82):add(segment(point(x,y),point(x+.10*sign,y),WHITE))
                for value,c,src,target,start in [
                    ("3",TEAL,floor((1.5,0))+point(-.02,-.53),point(3.47,1.56),89),
                    ("1",CORAL,floor((3,.47))+point(.25,0),point(3.47,1.06),92)]:
                    if s>=start:
                        f=ramp(s,start,start+2)
                        add(label(value,*((1-f)*src+f*target)[:2],23,c,True,center=True))
            if s>=98:
                tail=ramp(s,98,100)*np.array([-2.,1.])
                vector(tail,U,TEAL)
                add(Dot(floor(tail),radius=.044,color=TEAL))
                if s>=100:tag("copy",tail+U,-.32,.24,TEAL)
            if s>=101:side("New tip  (1, 2)",.42)
            if s>=106:side("Why is the command still (3, 1)?",-.24,21,GOLD)
            if s>=111:
                side("Tip minus tail",-1.08,20,MUTED)
                eq(r"(1-(-2),\,2-1)",-1.72)
                eq(r"=(3,1)",-2.44,TEAL)
        elif scene==3:
            if s<122:
                tail=(1-ramp(s,120,122))*np.array([-2.,1.])
                vector(tail,U,TEAL)
            vector(ZERO,U,TEAL,"u",(.16,-.16))
            if s>=125:
                add(move_arrow(ZERO,V*ramp(s,125,127),"#805958",3))
                tail=U*ramp(s,133,135)
                vector(tail,V*ramp(s,125,127),CORAL,"v",(-.35,.16))
            if s>=140:
                a,b=ramp(s,140,143),ramp(s,146,149)
                pos=bent(a,b)
                if s<158:add(robot(pos,U if s<146 else V))
            if s>=149:ring(GOAL)
            if s>=158:
                vector(ZERO,ramp(s,158,161)*GOAL,GOLD)
                if s>=161:tag("u + v",GOAL,.26,.20,GOLD)
            side("First command",2.37,20,TEAL)
            eq(r"u=\binom31",1.67,TEAL)
            if s>=125:
                side("Second command",.84,20,CORAL)
                eq(r"v=\binom{-1}2",.14,CORAL)
            if s>=151 and s<169:side("Same finish. One move?",-1.08,24,GOLD)
            if s>=169:
                guide((0,-.64),(3,-.64),TEAL)
                guide((3,-.92),(2,-.92),CORAL)
                tag("+3",(1.25,-.64),0,-.24,TEAL)
                tag("−1",(2.45,-.92),0,-.24,CORAL)
                eq(r"x:\quad 3+(-1)=2",-.91)
            if s>=174:eq(r"y:\quad 1+2=3",-1.60)
            if s>=180:eq(r"u+v=\binom23",-2.65,GOLD)
        elif scene==4:
            k=scalar(s)
            trail(np.array([-3.75,-1.25]),np.array([6.65,6.65/3]),DASH)
            add(move_arrow(ZERO,U,"#47776E",3))
            if s<251:
                if abs(k)<1e-10:add(Dot(floor(ZERO),radius=.069,color=TEAL))
                else:vector(ZERO,k*U,TEAL)
                tag("ku",k*U,-.13 if k<0 else .10,-.30 if k<0 else .24,TEAL)
            else:
                vector(ZERO,.5*U,TEAL,"½u",(.10,-.20))
                vector(.5*U,V*ramp(s,251,253),CORAL,"v",(-.39,.18))
                if s>=255:vector(ZERO,(.5*U+V)*ramp(s,255,257),GOLD)
            if s<240:
                side("Scale the displacement",2.34,27)
                eq(r"ku=(3k,k)",1.52,TEAL)
                x=2.24+(k+1)*1.29
                add(segment(point(2.24,.49),point(6.11,.49),DASH,3))
                for i in (-1,0,1,2):
                    xp=2.24+(i+1)*1.29
                    add(segment(point(xp,.40),point(xp,.58),MUTED,2))
                    add(label(str(i).replace("-","−"),xp,.13,19,MUTED,center=True))
                add(Dot(point(x,.49),radius=.087,color=TEAL))
                side("k = "+num(k),-.57,26)
                side("Tip   ("+num(3*k)+", "+num(k)+")",-1.35,29,TEAL)
                if s>=215 and s<219:side("Zero displacement",-2.20,22)
                if s>=221:side("Length factor = |k|",-2.20,22)
            else:
                side("Half the first move,",2.28,26)
                side("then all of the second.",1.77,26)
                if s<250:side("Where will it finish?",.67,24,GOLD)
                else:eq(r"\tfrac12 u+v",.74)
                if s>=253:eq(r"=(1.5,0.5)+(-1,2)",-.03)
                if s>=257:
                    eq(r"=(0.5,2.5)",-.89,GOLD)
                    side("Linear combination",-1.79,23,TEAL)
        else:
            bent(1,1);ring(GOAL)
            f=ramp(s,269,272)
            vector(ZERO,f*GOAL,GOLD)
            if s>=272:tag("u + v",GOAL,.25,.20,GOLD)
            add(robot(f*GOAL,GOAL))
            side("One direct command",2.37,28)
            eq(r"u+v=\binom23",1.52,GOLD)
            if s>=274:side("A vector records a position change.",.55,21)
            if s>=279:side("Addition combines displacements.",-.04,21)
            if s>=283:side("Scaling multiplies every component.",-.66,21)
            if s>=286:
                side("3Blue1Brown  ·  Chapter 1",-1.50,19,TEAL)
                side("Vectors, what even are they?",-1.91,20)
                side("Manim CE · Python · FFmpeg",-2.41,17,MUTED)
                side("Codex assisted with script, graphics and code.",-2.82,16,MUTED)
                side("Voice credit  ·  "+self.person["NARRATION_CREDIT"],-3.29,17)
        self.canvas.submobjects=nodes
