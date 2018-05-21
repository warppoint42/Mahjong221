# -*- coding: utf-8 -*-
import random
import logging

from game.ai.base.main import InterfaceAI
from mahjong.shanten import Shanten
from mahjong.agari import Agari
from mahjong.tile import TilesConverter

logger = logging.getLogger('ai')

class ImplementationAI(InterfaceAI):
    """
    AI that will discard random tile from the hand
    """
    version = 'shantenNaive'

    shanten = None
    agari = None

    def __init__(self, player):
        super(ImplementationAI, self).__init__(player)
        self.shanten = Shanten()
        self.agari = Agari()

    def discard_tile(self, discard_tile):
        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
        # is_agari = self.agari.is_agari(tiles_34, self.player.open_hand_34_tiles)

        results = []

        for tile in range(0,34):
            #Can the tile be discarded from the concealed hand?
            if not closed_tiles_34[tile]:
                continue

            #discard the tile from hand
            tiles_34[tile] -= 1

            #calculate shanten and store
            shanten = self.shanten.calculate_shanten(tiles_34, self.player.open_hand_34_tiles)
            results.append((shanten, tile))

            # return tile to hand
            tiles_34[tile] += 1

        (shanten, discard_34) = min(results)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        if discard_136 is None:
            logger.debug('Greedy search or tile conversion failed')
            discard_136 = random.randrange(len(self.player.tiles) - 1)
            discard_136 = self.player.tiles[discard_136]
        logger.debug('Shanten after discard:' + str(shanten))
        return discard_136

    def should_call_riichi(self):
        return False

    def should_call_win(self, tile, enemy_seat):
        return True

    #TODO: Verify that this method actually works
    def should_call_kan(self, tile, is_open_kan):
        """
        When bot can call kan or chankan this method will be called
        :param tile: 136 tile format
        :param is_open_kan: boolean
        :return: kan type (Meld.KAN, Meld.CHANKAN) or None
        """
        return is_open_kan
