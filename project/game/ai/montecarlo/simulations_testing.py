#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 00:10:46 2018

@author: nantanick
"""

from Shanten import Shanten
from mahjong.agari import Agari #checks for hands
from mahjong.tile import TilesConverter
from mahjong.meld import Meld
from mahjong.utils import is_man, is_pin, is_sou, is_pon, is_chi
import random
import copy
import numpy as np


# complete hand
# hand = TilesConverter.string_to_34_array(pin='112233999', honors='11177')
#unaccounted_tiles = np.array([4]*34)-hand    

#tenpai
#hand = TilesConverter.string_to_34_array(man='284', pin='24667',sou='1136', honors='77')
#unaccounted_tiles = np.array([4]*34)-hand
    
#terrible
#hand = TilesConverter.string_to_34_array(pin='112233',man='257',sou='345', honors='16')
    
def simulate_naive(hand, hand_open, unaccounted_tiles, turn):
    """
    #naive simulation

    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    shanten = Shanten()
    hand = copy.deepcopy(hand)
    unaccounted = copy.deepcopy(unaccounted_tiles)
    tiles_left = sum(unaccounted_tiles)
    unaccounted_nonzero = np.nonzero(unaccounted)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    for i in range(tiles_left - 53):
        if shanten.calculate_shanten(hand, hand_open) <= 0:#if tenpai
            return True
        hand_nonzero = np.nonzero(hand)[0] #discard something random
        discard = random.choice(hand_nonzero)
        hand[discard] -= 1
        unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted[draw_tile] -= 1
        hand[draw_tile] +=1
    return False

def simulate_naive2(hand, hand_open, unaccounted_tiles, turn):
    """
    #naive simulation

    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    shanten = Shanten()
    hand_changes = np.array([0]*34)
    unaccounted_changes = np.array([0]*34)
    tiles_left = sum(unaccounted_tiles)
    unaccounted_nonzero = np.nonzero(unaccounted_tiles)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    for i in range(tiles_left - 53):
        if shanten.calculate_shanten(hand, hand_open) <= 0:#if tenpai
            hand += hand_changes
            unaccounted_tiles += unaccounted_changes
            return True
        hand_nonzero = np.nonzero(hand)[0] #discard something random
        discard = random.choice(hand_nonzero)
        hand[discard] -= 1
        hand_changes[discard] += 1
        unaccounted_nonzero = np.nonzero(unaccounted_tiles)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted_tiles[draw_tile] -= 1
        unaccounted_changes[draw_tile] += 1
        hand[draw_tile] +=1
        hand_changes[draw_tile] -=1
    hand += hand_changes
    unaccounted_tiles += unaccounted_changes
    return False

def simulate_naive3(hand, hand_open, unaccounted_tiles, turn):
    """
    #naive simulation

    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    agari = Agari()
    hand_changes = np.array([0]*34)
    unaccounted_changes = np.array([0]*34)
    tiles_left = sum(unaccounted_tiles)
    unaccounted_nonzero = np.nonzero(unaccounted_tiles)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    for i in range(tiles_left - 53):
        if agari.is_agari(hand, hand_open):
            hand += hand_changes
            unaccounted_tiles += unaccounted_changes
            return True
        hand_nonzero = np.nonzero(hand)[0] #discard something random
        discard = random.choice(hand_nonzero)
        hand[discard] -= 1
        hand_changes[discard] += 1
        unaccounted_nonzero = np.nonzero(unaccounted_tiles)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted_tiles[draw_tile] -= 1
        unaccounted_changes[draw_tile] += 1
        hand[draw_tile] +=1
        hand_changes[draw_tile] -=1
    hand += hand_changes
    unaccounted_tiles += unaccounted_changes
    return False

def simulate_weighted(hand, hand_open, unaccounted_tiles, turn):
    """
    Does a weighted simulation
    
    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    shanten = Shanten()
    hand = copy.deepcopy(hand)
    unaccounted = copy.deepcopy(unaccounted_tiles)
    tiles_left = sum(unaccounted_tiles)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    for i in range(tiles_left - 53):
        if shanten.calculate_shanten(hand, hand_open) <= 0: #if tenpai
            return True
        hand_nonzero = np.nonzero(hand)[0]
        nonzero_inverted = [4-hand[i] for i in hand_nonzero]
        weight = np.array(nonzero_inverted)/sum(nonzero_inverted)
        discard = np.random.choice(hand_nonzero, 1, p = weight, replace=False)[0]
        hand[discard] -= 1
        #print(weight, nonzero_inverted)
        unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted[draw_tile] -= 1
        hand[draw_tile] +=1
    return False

def simulate_weighted2(hand, hand_open, unaccounted_tiles, turn):
    """
    Does a weighted simulation (Incomplete)
    
    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    shanten = Shanten()
    hand = copy.deepcopy(hand)
    unaccounted = copy.deepcopy(unaccounted_tiles)
    tiles_left = sum(unaccounted_tiles)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    for i in range(tiles_left - 53):
        if shanten.calculate_shanten(hand, None) <= 0:         
            return True
        weight = [0]*34
        for i, count in enumerate(hand):
            if count >=3:
                weight[i] = 0
            else:
                weight[i] = 4 - count
        weight = np.array(weight)/sum(weight)
        discard = np.random.choice(range(34), 1, p = weight, replace=False)[0]
        hand[discard] -= 1
        #print(weight, nonzero_inverted)
        unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted[draw_tile] -= 1
        hand[draw_tile] +=1
    return False

if __name__ == "__main__":
    hand = np.array(TilesConverter.string_to_34_array(man='284', pin='24667',sou='1136', honors='77'))
    unaccounted_tiles = np.array([4]*34)-hand 
    print(sum(simulate_naive(hand, [], unaccounted_tiles, 0) for _ in range(100)))
    #print(simulate_naive3(hand, [], unaccounted_tiles, 0))

#heuristics    
#keep more in the center
#throw away non consecutive
    
# try todo yakuhai   

# richi
# safe card
# throw away winds and dragons
# cards they discard the most
# random
# 3 away is dangerous (e.g. 5 -> 4,6,8,2)
    
# tiles_136 = TilesConverter.string_to_136_array(pin='112233999', honors='11177')

#hand = HandCalculator()
#player_wind = EAST
#
#tiles = self._string_to_136_array(pin='112233999', honors='11177')
#win_tile = self._string_to_136_tile(pin='9')
#melds = [
#    self._make_meld(Meld.PON, honors='111'),
#    self._make_meld(Meld.CHI, pin='123'),
#    self._make_meld(Meld.CHI, pin='123'),
#]
    

    