import asyncio
import numpy as np

from poke_env.player.player import Player
from poke_env.player.random_player import RandomPlayer
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ShowdownServerConfiguration

my_player_config = PlayerConfiguration("A80VE", "123456")


class MaxDamagePlayer(Player):

    def choose_move(self, battle):
        # If the player can attack, it will
        if battle.available_moves:
            # Finds the best move among available ones
            best_move = max(battle.available_moves,
                            key=lambda move: move.base_power)
            return self.create_order(best_move)

        # If no attack is available, a random switch will be made
        else:
            return self.choose_random_move(battle)

    def teampreview(self, battle):
        mon_performance = {}

        # For each of our pokemons
        for i, mon in enumerate(battle.team.values()):
            # We store their average performance against the opponent team
            mon_performance[i] = np.mean(
                [
                    teampreview_performance(mon, opp)
                    for opp in battle.opponent_team.values()
                ]
            )

        # We sort our mons by performance
        ordered_mons = sorted(
            mon_performance, key=lambda k: -mon_performance[k])

        # We start with the one we consider best overall
        # We use i + 1 as python indexes start from 0
        #  but showdown's indexes start from 1
        return "/team " + "".join([str(i + 1) for i in ordered_mons])


def teampreview_performance(mon_a, mon_b):
    # We evaluate the performance on mon_a against mon_b as its type advantage
    a_on_b = b_on_a = -np.inf
    for type_ in mon_a.types:
        if type_:
            a_on_b = max(a_on_b, type_.damage_multiplier(*mon_b.types))
    # We do the same for mon_b over mon_a
    for type_ in mon_b.types:
        if type_:
            b_on_a = max(b_on_a, type_.damage_multiplier(*mon_a.types))
    # Our performance metric is the different between the two
    return a_on_b - b_on_a


async def main():
    line_team = """Dragapult (F) @ Expert Belt  
Ability: Infiltrator  
EVs: 252 SpA / 4 SpD / 252 Spe  
Modest Nature  
IVs: 0 Atk  
- Hex  
- Draco Meteor  
- Thunder  
- Shadow Ball  

Clefable (F) @ Leftovers  
Ability: Magic Guard  
EVs: 252 HP / 4 Def / 252 SpD  
Calm Nature  
IVs: 0 Atk  
- Thunder Wave  
- Soft-Boiled  
- Calm Mind  
- Moonblast  

Toxapex (F) @ Black Sludge  
Ability: Regenerator  
EVs: 252 HP / 252 Def / 4 SpD  
Bold Nature  
IVs: 0 Atk  
- Scald  
- Toxic Spikes  
- Baneful Bunker  
- Recover  

Corviknight (F) @ Leftovers  
Ability: Pressure  
EVs: 252 HP / 252 Def / 4 SpD  
Impish Nature  
- Body Press  
- Iron Head  
- Defog  
- Roost  

Obstagoon (F) @ Flame Orb  
Ability: Guts  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Facade  
- Knock Off  
- Switcheroo  
- Bulk Up  

Hippowdon (M) @ Leftovers  
Ability: Sand Stream  
EVs: 248 HP / 8 Def / 252 SpD  
Careful Nature  
- Stealth Rock  
- Slack Off  
- Earthquake  
- Whirlwind  
"""

    max_damage_player = MaxDamagePlayer(
        battle_format="gen8ou",
        team=line_team,
        max_concurrent_battles=1,
        server_configuration=ShowdownServerConfiguration,
        player_configuration=my_player_config
    )

    await max_damage_player.ladder(5)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
