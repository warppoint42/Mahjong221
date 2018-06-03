#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 22:49:20 2018

@author: nantanick
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 00:10:46 2018

@author: nantanick
"""

from Shanten import Shanten
from mahjong.tile import TilesConverter
import random
import numpy as np



def simulate(hand, hand_open, unaccounted_tiles):
    """
    #naive simulation

    hand, hand_open -- hand in 34 format
    unaccounted_tiles -- all the unused tiles in 34 format
    turn -- a number from 0-3 (0 is the player)
    """
    shanten_calc = Shanten()
    hand = list(hand)
    unaccounted = list(unaccounted_tiles)
    tiles_left = sum(unaccounted_tiles)
    unaccounted_nonzero = np.nonzero(unaccounted)
    #14 in dead wall 13*3= 39 in other hand -> total 53
    shanten_sum = 0
    for i in range(tiles_left - 119):
        unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted[draw_tile] -= 1
        hand[draw_tile] +=1
        shanten = shanten_calc.calculate_shanten(hand, hand_open)
        if shanten <= 0:#if tenpai
            break
        shanten_sum += shanten **2
        hand_nonzero = np.nonzero(hand)[0] #discard something random
        discard = random.choice(hand_nonzero)
        hand[discard] -= 1
    return shanten_sum

def discard(hand, hand_open):
    unaccounted_tiles = np.array([4]*34)-hand 
    results = []
    for tile in range(0,34):
        #Can the tile be discarded from the concealed hand?
        if not hand[tile]:
            continue
        
        #discard the tile from hand
        hand[tile] -= 1

        #calculate shanten and store
        sim_util = sum(simulate(hand, hand_open, unaccounted_tiles) for _ in range(200))
        results.append((sim_util, tile))

        # return tile to hand
        hand[tile] += 1
    print(results)

    (sim_util, discard_34) = min(results)
    return discard_34
    

if __name__ == "__main__":
    #hand = np.array(TilesConverter.string_to_34_array(man='284', pin='24667',sou='113', honors='77'))
    #hand = np.array(TilesConverter.string_to_34_array(man='189', pin='2378',sou='2345', honors='15'))
    #hand = np.array(TilesConverter.string_to_34_array(pin='268',man='2579',sou='258', honors='135'))
#    
#    
#    #similar hands
#    hand = np.array(TilesConverter.string_to_34_array(man='189', pin='2378',sou='2345', honors='15'))
##    hand = np.array(TilesConverter.string_to_34_array(man='1894', pin='237',sou='2345', honors='15'))
##    hand = np.array(TilesConverter.string_to_34_array(man='1894', pin='2378',sou='2345', honors='1'))
#    
#    unaccounted_tiles = np.array([4]*34)-hand 
#    print([(sum(simulate(hand, [], unaccounted_tiles) for _ in range(100))) for _ in range(14)])
#    #print(simulate_naive3(hand, [], unaccounted_tiles, 0))
    print(discard(hand, []))
    
    

    