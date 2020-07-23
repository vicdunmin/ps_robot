import asyncio
import time
import numpy as np

from poke_env.player.player import Player
from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.server_configuration import ShowdownServerConfiguration


my_player_config = PlayerConfiguration("A80VE", "123456")
# If your server is accessible at my.custom.host:5432, and your authentication
# endpoint is authentication-endpoint.com/action.php?
my_server_config = ServerConfiguration(
    "https://china.psim.us/",
    "authentication-endpoint.com/action.php?"
)


class MaxDamagePlayer(Player):

    def switch(self, battle):
        if (len(battle.available_switches) == 0):
            return self.choose_random_move(battle)
        max_type_adv = -np.inf
        switch = None
        for pokemon in battle.available_switches:
            curr_type_adv = teampreview_performance(
                pokemon, battle.opponent_active_pokemon)
            if (curr_type_adv > max_type_adv):
                max_type_adv = curr_type_adv
                switch = pokemon
        return self.create_order(switch)

    def stayIn(self, battle):
        max_i = 4
        max_power = -1
        move_dmg_multiplier = 1
        selfType1 = battle.active_pokemon.type_1.name
        for i, move in enumerate(battle.available_moves):
            if move.type:
                move_dmg_multiplier = move.type.damage_multiplier(
                    battle.opponent_active_pokemon.type_1,
                    battle.opponent_active_pokemon.type_2,
                )
                if (move.type.name == selfType1):
                    move_dmg_multiplier *= 1.5
                elif (battle.active_pokemon.type_2 != None):
                    selfType2 = battle.active_pokemon.type_2.name
                    if (move.type.name == selfType2):
                        move_dmg_multiplier *= 1.5

            move_fpower = move.base_power * move_dmg_multiplier
            if (move_fpower > max_power):
                max_i = i
                max_power = move_fpower

        if (max_power < 70):
            return self.switch(battle)

        # Finds the best move among available ones
        # best_move = max(battle.available_moves, key=lambda move: move.base_power)
        else:
            return self.create_order(battle.available_moves[max_i])

    def choose_move(self, battle):
        if battle.available_moves and (teampreview_performance(battle.active_pokemon, battle.opponent_active_pokemon) <= -1):
            return self.switch(battle)

        # If the player can attack, it will
        elif battle.available_moves:
            return self.stayIn(battle)

        else:
            return self.switch(battle)

        # If no attack is available, a random switch will be made

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

    start = time.time()

    # # We create two players.
    # random_player = RandomPlayer(
    #     battle_format="gen8randombattle",
    # )

    # Now, let's evaluate our player
    # cross_evaluation = await cross_evaluate(
    #     [random_player, max_damage_player], n_challenges=100
    # )

    # print(
    #     "Max damage player won %d / 100 battles [this took %f seconds]"
    #     % (
    #         cross_evaluation[max_damage_player.username][random_player.username] * 100,
    #         time.time() - start,
    #     )
    # )

    max_damage_player = MaxDamagePlayer(
        battle_format="gen8ou",
        server_configuration=ShowdownServerConfiguration,
        player_configuration=my_player_config,
        team=line_team,
        max_concurrent_battles=1
    )
    await max_damage_player.ladder(5)

    # rb_player = MaxDamagePlayer(
    #     battle_format="gen8randombattle",
    #     server_configuration=ShowdownServerConfiguration,
    #     player_configuration=my_player_config,
    #     max_concurrent_battles=5
    # )

    # await rb_player.ladder(10)

    # for battle in player.battles.values():
    #     print(battle.rating, battle.opponent_rating)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
