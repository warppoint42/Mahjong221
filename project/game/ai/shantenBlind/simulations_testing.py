# -*- coding: utf-8 -*-
# import random
# import logging
# import copy
import cProfile

# from game.ai.base.main import InterfaceAI
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter
# from mahjong.meld import Meld
# from mahjong.utils import is_man, is_pin, is_sou, is_pon, is_chi
# from mahjong.hand_calculating.divider import HandDivider
import numpy as np

shantenCalc = Shanten()
shdict = {}

# def discard_tile(discard_tile):
#
#     if discard_tile is not None:
#         return discard_tile
#
#     tiles_34 = TilesConverter.to_34_array(self.player.tiles)
#     closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
#
#     results = []
#
#     for tile in range(0, 34):
#         # Can the tile be discarded from the concealed hand?
#         if not closed_tiles_34[tile]:
#             continue
#
#         # discard the tile from hand
#         tiles_34[tile] -= 1
#
#         # calculate shanten and store
#         shanten = shantenCalc.calculate_shanten(tiles_34, self.player.open_hand_34_tiles)
#         results.append((shanten, tile))
#
#         # return tile to hand
#         tiles_34[tile] += 1
#
#     (minshanten, discard_34) = min(results)
#
#     results2 = []
#
#     for shanten, tile in results:
#         if shanten != minshanten:
#             continue
#         h = calculate_outs(tile, shanten)
#         results2.append((h, tile))
#
#     (h, discard_34) = min(results2)
#
#     discard_136 = TilesConverter.find_34_tile_in_136_array(discard_34, self.player.closed_hand)
#
#     if discard_136 is None:
#         print('Failure')
#         discard_136 = random.randrange(len(self.player.tiles) - 1)
#         discard_136 = self.player.tiles[discard_136]
#     print('Shanten after discard:' + str(shanten))
#     print('Discard heuristic:' + str(h))
#     return discard_136

# def calculate_outs(discard_34, shanten, depth = 3):
#     closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
#     table_34 = copy.deepcopy(self.table.revealed_tiles)
#     tiles_34 = TilesConverter.to_34_array(self.player.tiles)
#     table_34[discard_34] += 1
#     closed_tiles_34[discard_34] -= 1
#     tiles_34[discard_34] -= 1
#
#     hidden_34 = np.array([4] * 34) - np.array(closed_tiles_34) - np.array(table_34)
#
#     # want to sample? use this
#     # reveal_num = sum(hidden_34)
#     # draw_p = [float(i)/reveal_num for i in hidden_34]
#     # draw = np.random.choice(34, p=draw_p)
#
#     return out_search(tiles_34, closed_tiles_34, hidden_34, depth, shanten - 1)

def out_search(tiles_34, closed_tiles_34, hidden_34, depth, shanten):
    outs = 0
    for i in range(34):
        if hidden_34[i] == 0:
            continue
        ct = hidden_34[i]

        # draw tile from hidden to concealed hand
        hidden_34[i] -= 1
        closed_tiles_34[i] += 1
        tiles_34[i] += 1

        for tile in range(0, 34):
            # Can the tile be discarded from the concealed hand?
            if not closed_tiles_34[tile]:
                continue

            # discard the tile from hand
            closed_tiles_34[tile] -= 1
            tiles_34[tile] -= 1

            tuple_34 = tuple(tiles_34)
            # calculate shanten and add outs if appropriate
            if tuple_34 in shdict.keys():
                sh = shdict[tuple_34]
            else:
                sh = shantenCalc.calculate_shanten(tiles_34, None)
                shdict[tuple_34] = sh
            if sh == shanten:
                if depth <= 1 or shanten == -1:
                    outs += 1
                else:
                    outs += ct * out_search(tiles_34, closed_tiles_34, hidden_34, depth - 1, shanten - 1)

            # return tile to hand
            closed_tiles_34[tile] += 1
            tiles_34[tile] += 1

        # return tile from closed hand to hidden
        hidden_34[i] += 1
        closed_tiles_34[i] -= 1
        tiles_34[i] -= 1

    return outs


closed_tiles_34 = TilesConverter.string_to_34_array(sou='347', pin='469', man='459', honors='2567')
tiles_34 = TilesConverter.string_to_34_array(sou='347', pin='469', man='459', honors='2567')
table_34 = [3] * 34
shanten = 5


# closed_tiles_34 = TilesConverter.to_34_array(self.player.closed_hand)
# table_34 = copy.deepcopy(self.table.revealed_tiles)
# tiles_34 = TilesConverter.to_34_array(self.player.tiles)
# table_34[discard_34] += 1
# closed_tiles_34[discard_34] -= 1
# tiles_34[discard_34] -= 1

hidden_34 = np.array([4] * 34) - np.array(closed_tiles_34) - np.array(table_34)

# want to sample? use this
# reveal_num = sum(hidden_34)
# draw_p = [float(i)/reveal_num for i in hidden_34]
# draw = np.random.choice(34, p=draw_p)


cProfile.run('print(out_search(tiles_34, closed_tiles_34, hidden_34, 3, shanten - 1))')
# print(out_search(tiles_34, closed_tiles_34, hidden_34, 3, shanten - 1))
