import random

class Territory:
    def __init__(self, id, x, y, resources, defense=0, owner=None, custom_data=None):
        self.id = id
        self.x = x
        self.y = y
        self.resources = resources
        self.defense = defense
        self.owner = owner
        self.neighbors = []
        self.custom_data = custom_data

    def __repr__(self):
        return f"Territory(ID: {self.id}, Owner: {self.owner}, Def: {self.defense}, Res: {self.resources})"

    def set_owner(self, new_owner):
        self.owner = new_owner

    def add_neighbor(self, neighbor_id):
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)

class GameMap:
    def __init__(self):
        self.territories = {}

    def add_territory(self, territory):
        self.territories[territory.id] = territory

    def get_territory(self, territory_id):
        return self.territories.get(territory_id)

    def connect_territories(self, id1, id2):
        t1 = self.get_territory(id1)
        t2 = self.get_territory(id2)
        if t1 and t2:
            t1.add_neighbor(id2)
            t2.add_neighbor(id1)

    def get_territories_by_owner(self, owner_id):
        return [t for t in self.territories.values() if t.owner == owner_id]

    def get_adjacent_enemy_territories(self, bot_id):
        enemy_territories = set()
        owned_territories = self.get_territories_by_owner(bot_id)
        for owned_t in owned_territories:
            for neighbor_id in owned_t.neighbors:
                neighbor_t = self.get_territory(neighbor_id)
                if neighbor_t and neighbor_t.owner != bot_id and neighbor_t.owner is not None:
                    enemy_territories.add(neighbor_t)
        return list(enemy_territories)


class Bot:
    def __init__(self, id, name, game_map, initial_resources=100):
        self.id = id
        self.name = name
        self.resources = initial_resources
        self.territories = []
        self.alliances = []
        self.game_map = game_map

    def __repr__(self):
        return f"Bot(ID: {self.id}, Name: {self.name}, Resources: {self.resources}, Territories: {len(self.territories)})"

    def add_territory(self, territory_id):
        if territory_id not in self.territories:
            self.territories.append(territory_id)
            territory = self.game_map.get_territory(territory_id)
            if territory:
                territory.set_owner(self.id)

    def remove_territory(self, territory_id):
        if territory_id in self.territories:
            self.territories.remove(territory_id)
            territory = self.game_map.get_territory(territory_id)
            if territory:
                territory.set_owner(None)

    def gain_resources(self, amount):
        self.resources += amount

    def spend_resources(self, amount):
        if self.resources >= amount:
            self.resources -= amount
            return True
        return False

    def form_alliance(self, other_bot_id):
        if other_bot_id not in self.alliances:
            self.alliances.append(other_bot_id)
            print(f"{self.name} сформировал альянс с Bot {other_bot_id}")

    def break_alliance(self, other_bot_id):
        if other_bot_id in self.alliances:
            self.alliances.remove(other_bot_id)
            print(f"{self.name} разорвал альянс с Bot {other_bot_id}")

    def is_allied_with(self, other_bot_id):
        return other_bot_id in self.alliances

    def choose_territory_to_attack(self):
        enemy_territories = self.game_map.get_adjacent_enemy_territories(self.id)
        if not enemy_territories:
            return None

        target_territory = min(enemy_territories, key=lambda t: t.defense)
        return target_territory

    def calculate_attack_power(self):
        return self.resources // 10 + random.randint(1, 10)

    def attack_territory(self, target_territory_id, all_bots):
        target_territory = self.game_map.get_territory(target_territory_id)
        if not target_territory or target_territory.owner == self.id:
            print(f"{self.name} не может атаковать территорию {target_territory_id}. Недоступна или уже принадлежит ему.")
            return False

        if target_territory.owner in self.alliances:
            print(f"{self.name} не может атаковать союзную территорию {target_territory_id}.")
            return False

        attacker_power = self.calculate_attack_power()
        defender_power = target_territory.defense

        for ally_id in self.alliances:
            ally_bot = all_bots.get(ally_id)
            if ally_bot:
                for ally_territory_id in ally_bot.territories:
                    ally_territory = self.game_map.get_territory(ally_territory_id)
                    if ally_territory and target_territory.id in ally_territory.neighbors:
                        attacker_power += ally_bot.resources // 20
                        print(f"Бонус к атаке от союзника {ally_bot.name}")
                        break

        if target_territory.owner and all_bots.get(target_territory.owner):
            defender_bot = all_bots[target_territory.owner]
            defender_power += (defender_bot.resources // 15)
            for ally_id in defender_bot.alliances:
                ally_bot = all_bots.get(ally_id)
                if ally_bot:
                    for ally_territory_id in ally_bot.territories:
                        ally_territory = self.game_map.get_territory(ally_territory_id)
                        if ally_territory and target_territory.id in ally_territory.neighbors:
                            defender_power += ally_bot.resources // 20
                            print(f"Бонус к защите от союзника {ally_bot.name}")
                            break

        print(f"{self.name} атакует территорию {target_territory.id} (Владелец: {target_territory.owner}). Сила атаки: {attacker_power}, Сила защиты: {defender_power}")

        if attacker_power > defender_power:
            print(f"{self.name} захватил территорию {target_territory.id}!")
            if target_territory.owner:
                all_bots[target_territory.owner].remove_territory(target_territory.id)
            self.add_territory(target_territory.id)
            self.spend_resources(attacker_power // 2)
            return True
        else:
            print(f"{self.name} не смог захватить территорию {target_territory.id}.")
            self.spend_resources(attacker_power)
            return False

    def reinforce_territory(self, territory_id):
        territory = self.game_map.get_territory(territory_id)
        if territory and territory.owner == self.id:
            cost = 10
            if self.spend_resources(cost):
                territory.defense += 5
                print(f"{self.name} усилил защиту территории {territory_id}. Новая защита: {territory.defense}")
                return True
            print(f"{self.name} не хватает ресурсов для усиления территории {territory_id}.")
            return False
        print(f"{self.name} не может усилить территорию {territory_id}. Она ему не принадлежит.")
        return False

    def choose_territory_to_reinforce(self):
        threatened_territories = []
        for owned_t_id in self.territories:
            owned_t = self.game_map.get_territory(owned_t_id)
            if owned_t:
                for neighbor_id in owned_t.neighbors:
                    neighbor_t = self.game_map.get_territory(neighbor_id)
                    if neighbor_t and neighbor_t.owner != self.id and neighbor_t.owner is not None:
                        threatened_territories.append(owned_t)
                        break

        if not threatened_territories:
            if self.territories:
                all_owned_territories = [self.game_map.get_territory(t_id) for t_id in self.territories if self.game_map.get_territory(t_id)]
                if all_owned_territories:
                    return min(all_owned_territories, key=lambda t: t.defense).id
            return None

        target_territory = min(threatened_territories, key=lambda t: t.defense)
        return target_territory.id

    def make_move(self, all_bots):
        action = random.choice(["attack", "reinforce", "propose_alliance"])

        if action == "attack":
            target = self.choose_territory_to_attack()
            if target:
                self.attack_territory(target.id, all_bots)
            else:
                print(f"{self.name} хотел атаковать, но не нашел цель.")
                target_reinforce = self.choose_territory_to_reinforce()
                if target_reinforce:
                    self.reinforce_territory(target_reinforce)

        elif action == "reinforce":
            target = self.choose_territory_to_reinforce()
            if target:
                self.reinforce_territory(target)
            else:
                print(f"{self.name} хотел усилить, но не нашел цель.")
                target_attack = self.choose_territory_to_attack()
                if target_attack:
                    self.attack_territory(target_attack.id, all_bots)

        elif action == "propose_alliance":
            possible_allies = [bot_id for bot_id in all_bots if bot_id != self.id and bot_id not in self.alliances]
            if possible_allies:
                target_bot_id = random.choice(possible_allies)
                target_bot = all_bots[target_bot_id]
                self.propose_alliance(target_bot, all_bots)
            else:
                print(f"{self.name} хотел предложить альянс, но не нашел подходящего кандидата.")

    def propose_alliance(self, other_bot, all_bots):
        print(f"{self.name} предлагает альянс {other_bot.name}")
        if other_bot.respond_to_alliance_proposal(self, all_bots):
            self.form_alliance(other_bot.id)
            other_bot.form_alliance(self.id)
        else:
            print(f"{other_bot.name} отклонил предложение альянса от {self.name}")

    def respond_to_alliance_proposal(self, proposing_bot, all_bots):
        if len(self.alliances) < 2:
            print(f"{self.name} принимает предложение альянса от {proposing_bot.name}")
            return True
        print(f"{self.name} отклоняет предложение альянса от {proposing_bot.name}")
        return False

class Game:
    def __init__(self, num_bots=2, map_width=5, map_height=5):
        self.game_map = GameMap()
        self.bots = {}
        self.current_turn = 0
        self.map_width = map_width
        self.map_height = map_height
        self._initialize_map(map_width, map_height)
        self._initialize_bots(num_bots)
        self._assign_initial_territories()

    def _initialize_map(self, width, height): 
        print("Инициализация карты...")
        territory_id = 0
        manual_biome_assignments = {
            25: "Пустыня", 33: "Пустыня", 34: "Пустыня", 35: "Пустыня",
            36: "Пустыня", 37: "Пустыня", 29: "Пустыня", 22: "Пустыня",
            30: "Пустыня", 38: "Пустыня", 39: "Пустыня", 31: "Пустыня",

            26: "Горы", 27: "Горы", 28: "Горы",

            0: "Море", 2: "Море", 3: "Море", 4: "Море", 5: "Море",
            14: "Море", 15: "Море", 23: "Море", 58: "Море", 32: "Море",
            24: "Море", 48: "Море", 40: "Море", 17: "Море", 18: "Море", 19: "Море",
            10: "Море", 8: "Море",

            51: "Лес", 60: "Лес", 59: "Лес", 53: "Лес", 54: "Лес",
            62: "Лес", 11: "Лес", 12: "Лес", 20: "Лес",
        }

        for y in range(height):
            for x in range(width):
                resources = random.randint(5, 20)
                defense = random.randint(0, 5)
                chosen_biome = manual_biome_assignments.get(territory_id, "Равнина")
                custom_data_for_sector = {"biome": chosen_biome, "sector_name": f"Sector {territory_id}"}
                territory = Territory(territory_id, x, y, resources, defense, custom_data=custom_data_for_sector)
                self.game_map.add_territory(territory)
                territory_id += 1

        for y in range(height):
            for x in range(width):
                current_id = y * width + x
                if x > 0: self.game_map.connect_territories(current_id, y * width + (x - 1))
                if x < width - 1: self.game_map.connect_territories(current_id, y * width + (x + 1))
                if y > 0: self.game_map.connect_territories(current_id, (y - 1) * width + x)
                if y < height - 1: self.game_map.connect_territories(current_id, (y + 1) * width + x)
        print(f"Карта с {len(self.game_map.territories)} территориями создана.")

    def _initialize_bots(self, num_bots):
        print(f"Инициализация {num_bots} ботов...")
        bot_names = ["Альфа", "Бета", "Гамма", "Дельта", "Эпсилон", "Дзета"]
        for i in range(num_bots):
            bot_id = f"bot_{i}"
            name = random.choice(bot_names)
            bot_names.remove(name)
            bot = Bot(bot_id, name, self.game_map)
            self.bots[bot_id] = bot
            print(f"Бот {bot.name} (ID: {bot.id}) создан.")

    def _assign_initial_territories(self):
        print("Назначение начальных территорий...")
        all_territories_ids = list(self.game_map.territories.keys())
        random.shuffle(all_territories_ids)

        num_territories_per_bot = len(all_territories_ids) // len(self.bots)
        for i, bot_id in enumerate(self.bots):
            for _ in range(num_territories_per_bot):
                if all_territories_ids:
                    territory_id = all_territories_ids.pop(0)
                    self.bots[bot_id].add_territory(territory_id)

        print("Начальные территории назначены.")

    def _update_resources(self):
        for bot in self.bots.values():
            for territory_id in bot.territories:
                territory = self.game_map.get_territory(territory_id)
                if territory:
                    bot.gain_resources(territory.resources)

    def run_turn(self):
        self.current_turn += 1
        print(f"\n--- Ход {self.current_turn} ---")
        self._update_resources()

        for bot_id in list(self.bots.keys()):
            bot = self.bots.get(bot_id)
            if bot:
                bot.make_move(self.bots)

        self.print_game_state()

    def print_game_state(self):
        print("\n=== Состояние Игры ===")
        for bot in self.bots.values():
            owned_territories_count = len(self.game_map.get_territories_by_owner(bot.id))
            print(f"{bot.name} (ID: {bot.id}): Ресурсы: {bot.resources}, Территории: {owned_territories_count}, Альянсы: {[self.bots[aid].name for aid in bot.alliances]}")

        print("\nТерритории по владельцам:")
        owner_map = {}
        for t in self.game_map.territories.values():
            owner_name = self.bots[t.owner].name if t.owner else "Нейтральная"
            if owner_name not in owner_map:
                owner_map[owner_name] = 0
            owner_map[owner_name] += 1
        for owner, count in owner_map.items():
            print(f"  {owner}: {count} территорий")

    def run_game(self, turns=10):
        print("Начало игры!")
        for _ in range(turns):
            self.run_turn()
        print("Игра окончена.")


def create_map_for_player(width: int, height: int):
    game_map = GameMap()
    territory_id = 0
    biomes = ["Равнина", "Поле", "Горы", "Лес", "Море"]
    for y in range(height):
        for x in range(width):
            resources = random.randint(5, 20)
            defense = random.randint(0, 3)
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                chosen_biome = "Море"
            else:
                idx = (x * 7 + y * 11 + territory_id) % 4
                chosen_biome = biomes[idx]
            custom_data = {"biome": chosen_biome, "sector_name": f"Sector {territory_id}"}
            territory = Territory(territory_id, x, y, resources, defense, custom_data=custom_data)
            game_map.add_territory(territory)
            territory_id += 1
    for y in range(height):
        for x in range(width):
            cid = y * width + x
            if x > 0:
                game_map.connect_territories(cid, y * width + (x - 1))
            if x < width - 1:
                game_map.connect_territories(cid, y * width + (x + 1))
            if y > 0:
                game_map.connect_territories(cid, (y - 1) * width + x)
            if y < height - 1:
                game_map.connect_territories(cid, (y + 1) * width + x)
    return game_map


if __name__ == "__main__":
    game = Game(num_bots=3, map_width=4, map_height=4)
    game.run_game(turns=5)