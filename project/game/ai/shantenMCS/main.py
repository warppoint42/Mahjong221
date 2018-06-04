# -*- coding: utf-8 -*-
import random
import logging
import copy

from game.ai.base.main import InterfaceAI
# from mahjong.shanten import Shanten
from game.ai.Shanten import Shanten
from mahjong.tile import TilesConverter
from mahjong.meld import Meld
from mahjong.utils import is_man, is_pin, is_sou, is_pon, is_chi
from mahjong.hand_calculating.divider import HandDivider
from mahjong.agari import Agari
import numpy as np

logger = logging.getLogger('ai')

class ImplementationAI(InterfaceAI):
    """
    AI that will discard tiles to maximize expected shanten.
    Assumes that tiles are drawn randomly from those not on the table or in hand - aka not revealed to player.
    Does not account for hidden tiles in opponent's hands.
    Always calls wins, never calls riichi.
    TODO: Everything
    """
    version = 'shantenMCS'

    shanten = None
    agari = None
    shdict = {}

    def __init__(self, player):
        super(ImplementationAI, self).__init__(player)
        self.shanten = Shanten()
        self.hand_divider = HandDivider()
        self.agari = Agari()

    def simulate_single(self, hand, hand_open, unaccounted_tiles):
        """
        #simulates a single random draw and calculates shanten

        hand, hand_open -- hand in 34 format
        unaccounted_tiles -- all the unused tiles in 34 format
        turn -- a number from 0-3 (0 is the player)
        """

        hand = list(hand)
        unaccounted = list(unaccounted_tiles)
        #14 in dead wall 13*3= 39 in other hand -> total 53
        unaccounted_nonzero = np.nonzero(unaccounted)[0] #get a random card
        draw_tile = random.choice(unaccounted_nonzero)
        unaccounted[draw_tile] -= 1
        hand[draw_tile] += 1
        return self.shanten.calculate_shanten(hand, hand_open)

    # TODO: Merge all discard functions into one to prevent code reuse and unnecessary duplication of variables
    def discard_tile(self, discard_tile):

        if discard_tile is not None:
            return discard_tile

        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)

        results = []

        for tile in range(0, 34):
            # Can the tile be discarded from the concealed hand?
            if not closed_tiles_34[tile]:
                continue

            # discard the tile from hand
            tiles_34[tile] -= 1

            # calculate shanten and store
            shanten = self.shanten.calculate_shanten(tiles_34, self.player.open_hand_34_tiles)
            results.append((shanten, tile))

            # return tile to hand
            tiles_34[tile] += 1

        (minshanten, discard_34) = min(results)

        results2 = []
        unaccounted = (np.array([4]*34) - closed_tiles_34)\
            - TilesConverter.to_34_array(self.table.revealed_tiles)

        self.shdict = {}
        for shanten, tile in results:
            if shanten != minshanten:
                continue
            tiles_34[tile] -= 1
            h = sum(self.simulate_single(tiles_34, self.player.open_hand_34_tiles, unaccounted) for _ in range(1000))
            tiles_34[tile] += 1
            results2.append((h, tile))

        (h, discard_34) = min(results2)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        if discard_136 is None:
            logger.debug('Failure')
            discard_136 = random.randrange(len(self.player.tiles) - 1)
            discard_136 = self.player.tiles[discard_136]
        logger.info('Shanten after discard:' + str(shanten))
        logger.info('Discard heuristic:' + str(h))
        return discard_136

    # UNUSED
    def calculate_outs(self, discard_34, shanten, depth=2):
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
        table_34 = list(self.table.revealed_tiles)
        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        table_34[discard_34] += 1
        closed_tiles_34[discard_34] -= 1
        tiles_34[discard_34] -= 1

        hidden_34 = np.array([4] * 34) - np.array(closed_tiles_34) - np.array(table_34)

        # print(hidden_34)

        # want to sample? use this
        # reveal_num = sum(hidden_34)
        # draw_p = [float(i)/reveal_num for i in hidden_34]
        # draw = np.random.choice(34, p=draw_p)

        return self.out_search(tiles_34, closed_tiles_34, hidden_34, depth, shanten - 1)

    def calculate_outs_meld(self, discard_34, shanten, tiles_34, closed_tiles_34, open_hand_34, depth=2):
        table_34 = list(self.table.revealed_tiles)
        tiles_34 = copy.deepcopy(tiles_34)
        closed_tiles_34 = copy.deepcopy(closed_tiles_34)
        table_34[discard_34] += 1
        closed_tiles_34[discard_34] -= 1
        tiles_34[discard_34] -= 1

        hidden_34 = np.array([4] * 34) - np.array(closed_tiles_34) - np.array(table_34)

        return self.out_search(tiles_34, closed_tiles_34, hidden_34, depth, shanten - 1, open_hand_34)

    def out_search(self, tiles_34, closed_tiles_34, hidden_34, depth, shanten, open_hand_34=None):
        outs = 0
        for i in range(34):
            if hidden_34[i] <= 0:
                continue
            ct = hidden_34[i]

            # draw tile from hidden to concealed hand
            hidden_34[i] -= 1
            closed_tiles_34[i] += 1
            tiles_34[i] += 1

            if self.agari.is_agari(tiles_34, open_hand_34):
                outs += 2
            else:
                for tile in range(0, 34):
                    # Can the tile be discarded from the concealed hand?
                    if not closed_tiles_34[tile]:
                        continue

                    # discard the tile from hand
                    closed_tiles_34[tile] -= 1
                    tiles_34[tile] -= 1

                    tuple_34 = tuple(tiles_34)
                    # calculate shanten and add outs if appropriate
                    if tuple_34 in self.shdict.keys():
                        sh = self.shdict[tuple_34]
                    else:
                        if open_hand_34 is None:
                            sh = self.shanten.calculate_shanten(tiles_34, self.player.open_hand_34_tiles)
                        else:
                            sh = self.shanten.calculate_shanten(tiles_34, open_hand_34)
                        self.shdict[tuple_34] = sh
                    if sh == shanten:
                        if depth <= 1 or shanten == -1:
                            outs += 1
                        else:
                            outs += ct * self.out_search(tiles_34, closed_tiles_34, hidden_34, depth - 1, shanten - 1)
                    if sh == shanten + 1:
                        outs += 0.01

                    # return tile to hand
                    closed_tiles_34[tile] += 1
                    tiles_34[tile] += 1

            # return tile from closed hand to hidden
            hidden_34[i] += 1
            closed_tiles_34[i] -= 1
            tiles_34[i] -= 1

        return outs

    def should_call_riichi(self):
        # if len(self.player.open_hand_34_tiles) != 0:
        #     return False
        return True
        # tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        # shanten = self.shanten.calculate_shanten(tiles_34, None)
        # logger.debug('Riichi check, shanten = ' + str(shanten))
        # return shanten == 0

    def should_call_win(self, tile, enemy_seat):
        return True

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

    def try_to_call_meld(self, tile, is_kamicha_discard):
        """
        When bot can open hand with a set (chi or pon/kan) this method will be called
        :param tile: 136 format tile
        :param is_kamicha_discard: boolean
        :return: Meld and DiscardOption objects or None, None
        """

        # can't call if in riichi
        if self.player.in_riichi:
            return None, None

        closed_hand = self.player.closed_hand[:]

        # check for appropriate hand size, seems to solve a bug
        if len(closed_hand) == 1:
            return None, None

        # get old shanten value
        old_tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        old_shanten = self.shanten.calculate_shanten(old_tiles_34, self.player.open_hand_34_tiles)

        # setup
        discarded_tile = tile // 4
        new_closed_hand_34 = TilesConverter.to_34_array(closed_hand + [tile])

        # We will use hand_divider to find possible melds involving the discarded tile.
        # Check its suit and number to narrow the search conditions
        # skipping this will break the default mahjong functions
        combinations = []
        first_index = 0
        second_index = 0
        if is_man(discarded_tile):
            first_index = 0
            second_index = 8
        elif is_pin(discarded_tile):
            first_index = 9
            second_index = 17
        elif is_sou(discarded_tile):
            first_index = 18
            second_index = 26

        if second_index == 0:
            # honor tiles
            if new_closed_hand_34[discarded_tile] == 3:
                combinations = [[[discarded_tile] * 3]]
        else:
            # to avoid not necessary calculations
            # we can check only tiles around +-2 discarded tile
            first_limit = discarded_tile - 2
            if first_limit < first_index:
                first_limit = first_index

            second_limit = discarded_tile + 2
            if second_limit > second_index:
                second_limit = second_index

            combinations = self.hand_divider.find_valid_combinations(new_closed_hand_34,
                                                                     first_limit,
                                                                     second_limit, True)
        # Reduce combinations to list of melds
        if combinations:
            combinations = combinations[0]

        # Verify that a meld can be called
        possible_melds = []
        for meld_34 in combinations:
            # we can call pon from everyone
            if is_pon(meld_34) and discarded_tile in meld_34:
                if meld_34 not in possible_melds:
                    possible_melds.append(meld_34)

            # we can call chi only from left player
            if is_chi(meld_34) and is_kamicha_discard and discarded_tile in meld_34:
                if meld_34 not in possible_melds:
                    possible_melds.append(meld_34)

        # For each possible meld, check if calling it and discarding can improve shanten
        new_shanten = float('inf')
        discard_136 = None
        tiles = None

        for meld_34 in possible_melds:
            shanten, disc = self.meldDiscard(meld_34, tile)
            if shanten < new_shanten:
                new_shanten, discard_136 = shanten, disc
                tiles = meld_34

        # If shanten can be improved by calling meld, call it
        if new_shanten < old_shanten:
            meld = Meld()
            meld.type = is_chi(tiles) and Meld.CHI or Meld.PON

            # convert meld tiles back to 136 format for Meld type return
            # find them in a copy of the closed hand and remove
            tiles.remove(discarded_tile)

            first_tile = TilesConverter.find_34_tile_in_136_array(tiles[0], closed_hand)
            closed_hand.remove(first_tile)

            second_tile = TilesConverter.find_34_tile_in_136_array(tiles[1], closed_hand)
            closed_hand.remove(second_tile)

            tiles_136 = [
                first_tile,
                second_tile,
                tile
            ]

            discard_136 = TilesConverter.find_34_tile_in_136_array(discard_136 // 4, closed_hand)
            meld.tiles = sorted(tiles_136)
            return meld, discard_136

        return None, None

    # TODO: Merge all discard functions into one to prevent code reuse and unnecessary duplication of variables
    def meldDiscard(self, meld_34, discardtile):

        tiles_34 = TilesConverter.to_34_array(self.player.tiles + [discardtile])
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand + [discardtile])
        open_hand_34 = copy.deepcopy(self.player.open_hand_34_tiles)

        # remove meld from closed and and add to open hand
        open_hand_34.append(meld_34)
        for tile_34 in meld_34:
            closed_tiles_34[tile_34] -= 1

        results = []

        for tile in range(0, 34):

            # Can the tile be discarded from the concealed hand?
            if not closed_tiles_34[tile]:
                continue

            # discard the tile from hand
            tiles_34[tile] -= 1

            # calculate shanten and store
            shanten = self.shanten.calculate_shanten(tiles_34, open_hand_34)
            results.append((shanten, tile))

            # return tile to hand
            tiles_34[tile] += 1

        (minshanten, discard_34) = min(results)

        results2 = []
        unaccounted = (np.array([4]*34) - closed_tiles_34)\
            - TilesConverter.to_34_array(self.table.revealed_tiles)

        self.shdict = {}
        for shanten, tile in results:
            if shanten != minshanten:
                continue
            tiles_34[tile] -= 1
            h = sum(self.simulate_single(tiles_34, open_hand_34, unaccounted) for _ in range(10000))
            tiles_34[tile] += 1
            results2.append((h, tile))

        (h, discard_34) = min(results2)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        return minshanten, discard_136
