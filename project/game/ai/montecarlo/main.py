# -*- coding: utf-8 -*-
import random
import logging

from game.ai.base.main import InterfaceAI
from mahjong.shanten import Shanten
from mahjong.agari import Agari
from mahjong.tile import TilesConverter
from mahjong.meld import Meld
import numpy as np


logger = logging.getLogger('ai')

class ImplementationAI(InterfaceAI):
    """
    AI that will discard tiles as to minimimize shanten, using perfect shanten calculation.
    Picks the first tile with resulting in the lowest shanten value.
    Never calls riichi, always calls wins.
    Calls kan to upgrade pon or reduce shanten.
    TODO: Add calling melds
    """
    version = 'montecarlo'

    shanten = None
    agari = None

    def __init__(self, player):
        super(ImplementationAI, self).__init__(player)
        self.shanten = Shanten()
        self.agari = Agari()
        
    
    def simulate(self, hand, hand_open, unaccounted_tiles):
        """
        #simulation
    
        hand, hand_open -- hand in 34 format
        unaccounted_tiles -- all the unused tiles in 34 format
        turn -- a number from 0-3 (0 is the player)
        """
                
        hand = list(hand)
        unaccounted = list(unaccounted_tiles)
        tiles_left = sum(unaccounted_tiles)
        unaccounted_nonzero = np.nonzero(unaccounted)
        #14 in dead wall 13*3= 39 in other hand -> total 53
        shanten_sum = 0
        for i in range(min(tiles_left, 17)):
            unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
            draw_tile = random.choice(unaccounted_nonzero)
            unaccounted[draw_tile] -= 1
            hand[draw_tile] +=1
            shanten = self.shanten.calculate_shanten(hand, hand_open)
            if shanten <= 0:#if tenpai
                break
            shanten_sum += shanten**2
            hand_nonzero = np.nonzero(hand)[0] #discard something random
            discard = random.choice(hand_nonzero)
            hand[discard] -= 1
        return shanten_sum

    def discard_tile(self, discard_tile):
        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
        # is_agari = self.agari.is_agari(tiles_34, self.player.open_hand_34_tiles)

        results = []
        
        for tile in range(0,34):
            #Can the tile be discarded from the concealed hand?
            if not closed_tiles_34[tile]:
                continue
            
            unaccounted = (np.array([4]*34) - tiles_34)\
                - TilesConverter.to_34_array(self.table.revealed_tiles)
            #discard the tile from hand
            closed_tiles_34[tile] -= 1

            #calculate shanten and store
            sim_util = sum(self.simulate(closed_tiles_34, self.player.open_hand_34_tiles, unaccounted) for _ in range(200))
            results.append((sim_util, tile))

            # return tile to hand
            closed_tiles_34[tile] += 1

        (sim_util, discard_34) = min(results)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        if discard_136 is None:
            logger.debug('Greedy search or tile conversion failed')
            discard_136 = random.randrange(len(self.player.tiles) - 1)
            discard_136 = self.player.tiles[discard_136]
        logger.debug('Utility after discard:' + str(sim_util))
        return discard_136
    

    def should_call_riichi(self):
        return True
#        if len(self.player.open_hand_34_tiles) != 0:
#            return False
#        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
#        shanten = self.shanten.calculate_shanten(tiles_34, None)
#        return shanten == 0

    def should_call_win(self, tile, enemy_seat):
        return True

    #TODO: Verify that this method actually works
    def should_call_kan(self, tile, open_kan):
        """
        When bot can call kan or chankan this method will be called
        :param tile: 136 tile format
        :param is_open_kan: boolean
        :return: kan type (Meld.KAN, Meld.CHANKAN) or None
        """

        if open_kan:
            #  don't start open hand from called kan
            if not self.player.is_open_hand:
                return None

            # don't call open kan if not waiting for win
            if not self.player.in_tempai:
                return None

        tile_34 = tile // 4
        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        closed_hand_34 = TilesConverter.to_34_array(self.player.closed_hand)
        pon_melds = [x for x in self.player.open_hand_34_tiles if is_pon(x)]


        # upgrade open pon to kan if possible
        if pon_melds:
            for meld in pon_melds:
                if tile_34 in meld:
                    return Meld.CHANKAN

        count_of_needed_tiles = 4
        # for open kan 3 tiles is enough to call a kan
        if open_kan:
            count_of_needed_tiles = 3

        if closed_hand_34[tile_34] == count_of_needed_tiles:
            if not open_kan:
                # to correctly count shanten in the hand
                # we had do subtract drown tile
                tiles_34[tile_34] -= 1

            melds = self.player.open_hand_34_tiles
            previous_shanten = self.shanten.calculate_shanten(tiles_34, melds)

            melds += [[tile_34, tile_34, tile_34]]
            new_shanten = self.shanten.calculate_shanten(tiles_34, melds)

            # check for improvement in shanten
            if new_shanten <= previous_shanten:
                return Meld.KAN

        return None

    # def try_to_call_meld(self, tile, is_kamicha_discard):
    #     """
    #     When bot can open hand with a set (chi or pon/kan) this method will be called
    #     :param tile: 136 format tile
    #     :param is_kamicha_discard: boolean
    #     :return: Meld and DiscardOption objects or None, None
    #     """
    #
    #     # can't call if in riichi
    #     if self.player.in_riichi:
    #         return None, None
    #
    #     closed_hand = self.player.closed_hand[:]
    #
    #     # check for appropriate hand size, seems to solve a bug
    #     if len(closed_hand) == 1:
    #         return None, None
    #
    #
    #     discarded_tile = tile // 4
    #     new_tiles = self.player.tiles[:] + [tile]
    #     new_tiles_34 = TilesConverter.to_34_array(new_tiles)
    #     old_tiles_34 = TilesConverter.to_34_array(self.player.tiles)
    #     new_closed_hand_34 = TilesConverter.to_34_array(closed_hand + [tile])
    #     melds = self.player.open_hand_34_tiles
    #
    #     oldshanten = self.shanten.calculate_shanten(old_tiles_34, melds)
    #     newshanten, discard_136 =
    #     Meld.
    #
    #     return None, None
    #
    # def discardShanten(self, new_tiles_34, new_closed_hand_34, melds, newMeld):
    #     results = []
    #
    #
    #     for tile in range(0, 34):
    #
    #         for tile_34 in newMeld:
    #             new_tiles_34[tile_34] -= 1
    #             new_closed_hand_34[tile_34] -= 1
    #
    #         # Can the tile be discarded from the concealed hand?
    #         if not new_closed_hand_34[tile]:
    #             continue
    #
    #         # discard the tile from hand
    #         new_tiles_34[tile] -= 1
    #
    #         # calculate shanten and store
    #         shanten = self.shanten.calculate_shanten(new_tiles_34, melds)
    #         results.append((shanten, tile))
    #
    #         # return tile to hand
    #         for tile_34 in newMeld:
    #             new_tiles_34[tile_34] += 1
    #             new_closed_hand_34[tile_34] += 1
    #
    #     (shanten, discard_34) = min(results)
    #
    #     discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)
    #
    #     return shanten, discard_136
