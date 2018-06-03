# -*- coding: utf-8 -*-
import random
import logging
import copy

from game.ai.base.main import InterfaceAI
from mahjong.shanten import Shanten
# from mahjong.agari import Agari
from mahjong.tile import TilesConverter
from mahjong.meld import Meld
from mahjong.utils import is_man, is_pin, is_sou, is_pon, is_chi
from mahjong.hand_calculating.divider import HandDivider

logger = logging.getLogger('ai')

class ImplementationAI(InterfaceAI):
    """
    AI that will discard tiles as to minimize shanten, using perfect shanten calculation.
    Picks the first tile with resulting in the lowest shanten value when choosing what to discard.
    Calls riichi if possible and hand is closed.
    Always calls wins.
    Calls kan to upgrade pon or on equivalent or reduced shanten.
    Calls melds to reduce shanten.
    """
    version = 'shantenNaive'

    shanten = None
    agari = None

    def __init__(self, player):
        super(ImplementationAI, self).__init__(player)
        self.shanten = Shanten()
        # self.agari = Agari()
        self.hand_divider = HandDivider()

    # TODO: Merge all discard functions into one to prevent code reuse and unnecessary duplication of variables
    def discard_tile(self, discard_tile):

        if discard_tile is not None:
            return discard_tile

        tiles_34 = TilesConverter.to_34_array(self.player.tiles)
        closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
        # is_agari = self.agari.is_agari(tiles_34, self.player.open_hand_34_tiles)

        results = []

        for tile in range(0,34):
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

        (shanten, discard_34) = min(results)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        if discard_136 is None:
            logger.debug('Greedy search or tile conversion failed')
            discard_136 = random.randrange(len(self.player.tiles) - 1)
            discard_136 = self.player.tiles[discard_136]
        logger.info('Shanten after discard:' + str(shanten))
        return discard_136

    def should_call_riichi(self):
        if len(self.player.open_hand_34_tiles) != 0:
            return False
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

        (shanten, discard_34) = min(results)

        discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)

        return shanten, discard_136
