import random
import json
import os
PLAYER_ID = "player"
CAPTURE_COST = 1000
CAPTURE_RESOURCES = {"Камень": 15, "Дерево": 10, "Железная руда": 5}
PRODUCTION_INCOME_PER_BUILDING = 15
NO_PRODUCTION_PENALTY = 20
MINE_COST = 100
BED_COST = 50
SAWMILL_COST = 80

MINE_PRODUCES = {"Камень": (2, 5), "Железная руда": (1, 3), "Уголь": (1, 4)}
BED_PRODUCES = {"Пшеница": (2, 4), "Морковь": (1, 3), "Картофель": (2, 5)}
SAWMILL_PRODUCES = {"Дерево": (3, 6)}

MINE_BIOMES = ["Горы", "Лес"]
BED_BIOMES = ["Равнина", "Поле"]
SAWMILL_BIOMES = ["Лес"]

MINE_BUILD_RESOURCES = {"Камень": 10, "Дерево": 5}
BED_BUILD_RESOURCES = {"Дерево": 5}
SAWMILL_BUILD_RESOURCES = {"Камень": 5, "Железная руда": 2}

RESOURCE_NAMES = {"Coal": "Уголь", "Iron": "Железо", "Iron_ore": "Железная руда",
                  "Stone": "Камень", "Wood": "Дерево", "Wheat": "Пшеница",
                  "Carrot": "Морковь", "Potato": "Картофель"}


class Country:
    def __init__(self, country_id: str, name: str):
        self.id = country_id
        self.name = name
        self.territories = []
        self.inventory = {}
        if country_id == PLAYER_ID:
            self.inventory.update({"Камень": 40, "Дерево": 30, "Железная руда": 15})
        else:
            
            self.inventory.update({"Камень": 50, "Дерево": 40, "Железная руда": 20, "Уголь": 10})
        self.balance = 10000 if country_id == PLAYER_ID else 1500  
        self.alliances = []
        self.wars = []
        self.is_player = country_id == PLAYER_ID

    def add_territory(self, territory_id: int, game_map):
        if territory_id not in self.territories:
            self.territories.append(territory_id)
            t = game_map.get_territory(territory_id)
            if t:
                t.set_owner(self.id)

    def remove_territory(self, territory_id: int, game_map):
        if territory_id in self.territories:
            self.territories.remove(territory_id)
            t = game_map.get_territory(territory_id)
            if t:
                t.set_owner(None)

    def get_bordering_country_ids(self, game_map, all_countries: dict):
        bordering = set()
        for tid in self.territories:
            t = game_map.get_territory(tid)
            if not t:
                continue
            for nid in t.neighbors:
                nt = game_map.get_territory(nid)
                if nt and nt.owner and nt.owner != self.id:
                    bordering.add(nt.owner)
        return list(bordering)

    def add_resource(self, name: str, amount: int):
        self.inventory[name] = self.inventory.get(name, 0) + amount

    def remove_resource(self, name: str, amount: int) -> bool:
        cur = self.inventory.get(name, 0)
        if cur >= amount:
            self.inventory[name] = cur - amount
            if self.inventory[name] == 0:
                del self.inventory[name]
            return True
        return False

    def has_resource(self, name: str, amount: int = 1) -> bool:
        return self.inventory.get(name, 0) >= amount

    def has_resources_pack(self, costs: dict[str, int]) -> bool:
        return all(self.has_resource(name, amount) for name, amount in costs.items())

    def spend_resources_pack(self, costs: dict[str, int]) -> bool:
        if not self.has_resources_pack(costs):
            return False
        for name, amount in costs.items():
            self.remove_resource(name, amount)
        return True

    def spend_resources(self, amount: int) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False


class GameState:
    def __init__(self, map_width=8, map_height=8):
        self.map_width = map_width
        self.map_height = map_height
        self.countries = {}
        self.player_country = None
        self.selected_sector_id = None
        self.game_started = False
        self.game_map = None

    def save_game(self, save_name: str) -> bool:
        if not self.game_started:
            return False
            
        base_dir = os.path.dirname(os.path.abspath(__file__))
        saves_dir = os.path.join(base_dir, "..", "..", "assets", "saves")
        if not os.path.exists(saves_dir):
            os.makedirs(saves_dir)
            
        save_path = os.path.join(saves_dir, f"{save_name}.json")

        save_data = {
            "player_country": {
                "id": self.player_country.id,
                "name": self.player_country.name,
                "balance": self.player_country.balance,
                "inventory": self.player_country.inventory,
                "territories": self.player_country.territories,
                "alliances": self.player_country.alliances,
                "wars": self.player_country.wars
            },
            "countries": {},
            "game_map": {
                "territories": {}
            }
        }
        
        
        for cid, country in self.countries.items():
            save_data["countries"][cid] = {
                "id": country.id,
                "name": country.name,
                "balance": country.balance,
                "inventory": country.inventory,
                "territories": country.territories,
                "alliances": country.alliances,
                "wars": country.wars
            }
        
        
        for tid, territory in self.game_map.territories.items():
            save_data["game_map"]["territories"][str(tid)] = {
                "id": territory.id,
                "x": territory.x,
                "y": territory.y,
                "resources": territory.resources,
                "defense": territory.defense,
                "owner": territory.owner,
                "neighbors": territory.neighbors,
                "custom_data": territory.custom_data
            }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения игры: {e}")
            return False

    def load_game(self, save_name: str) -> bool:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        saves_dir = os.path.join(base_dir, "..", "..", "assets", "saves")
        save_path = os.path.join(saves_dir, f"{save_name}.json")

        if not os.path.exists(save_path):
            return False
            
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
           
            player_data = save_data["player_country"]
            self.player_country = Country(player_data["id"], player_data["name"])
            self.player_country.balance = player_data["balance"]
            self.player_country.inventory = player_data["inventory"]
            self.player_country.territories = player_data["territories"]
            self.player_country.alliances = player_data["alliances"]
            self.player_country.wars = player_data["wars"]
            
            
            self.countries = {}
            for cid, country_data in save_data["countries"].items():
                country = Country(country_data["id"], country_data["name"])
                country.balance = country_data["balance"]
                country.inventory = country_data["inventory"]
                country.territories = country_data["territories"]
                country.alliances = country_data["alliances"]
                country.wars = country_data["wars"]
                self.countries[cid] = country
            
            
            map_data = save_data["game_map"]
            for tid_str, territory_data in map_data["territories"].items():
                tid = int(tid_str)
                if self.game_map and self.game_map.territories:
                    territory = self.game_map.get_territory(tid)
                    if territory:
                        territory.owner = territory_data["owner"]
                        territory.custom_data = territory_data["custom_data"]
            
            self.game_started = True
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки игры: {e}")
            return False

    def get_save_list(self) -> list:
        base_dir = os.path.dirname(os.path.abspath(__file__))

        candidates = [
            os.path.join(base_dir, "assets", "saves"),
            os.path.join(base_dir, "..", "assets", "saves"),
            os.path.join(base_dir, "..", "..", "assets", "saves"),
        ]
        saves_dir = None
        for c in candidates:
            if os.path.isdir(c):
                saves_dir = c
                break
        if saves_dir is None:
            saves_dir = candidates[0]

        if not os.path.exists(saves_dir):
            return []
            
        saves = []
        for file in os.listdir(saves_dir):
            if file.endswith('.json'):
                save_name = file[:-5]  
                saves.append(save_name)
        return sorted(saves)

    def init_for_map(self, game_map):
        self.game_map = game_map

    def create_player_country(self, name: str, start_sector_id: int):
        if self.player_country:
            return False
        c = Country(PLAYER_ID, name)
        self.countries[PLAYER_ID] = c
        c.add_territory(start_sector_id, self.game_map)
        self.player_country = c
        self.game_started = True
        return True

    def get_player_bordering_countries(self):
        if not self.player_country or not self.game_map:
            return []
        return self.player_country.get_bordering_country_ids(
            self.game_map, self.countries
        )

    def can_trade_with(self, country_id: str) -> bool:
        return country_id in self.get_player_bordering_countries()

    def count_buildings(self, country: Country) -> int:
        building_count = 0
        for tid in country.territories:
            t = self.game_map.get_territory(tid)
            if t and t.custom_data and t.custom_data.get("building"):
                building_count += 1
        return building_count

    def apply_production_income(self, country: Country):
        building_count = self.count_buildings(country)
        
        if building_count > 0:
         
            income = building_count * PRODUCTION_INCOME_PER_BUILDING
            country.balance += income
            return f"+{income}₽ доход от {building_count} производств"
        else:
           
            country.balance = max(0, country.balance - NO_PRODUCTION_PENALTY)
            return f"-{NO_PRODUCTION_PENALTY}₽ штраф за отсутствие производств"

    def get_adjacent_sectors(self, sector_id: int):
        t = self.game_map.get_territory(sector_id) if self.game_map else None
        if not t:
            return []
        return t.neighbors

    def can_capture_sector(self, sector_id: int) -> tuple[bool, str]:
        if not self.player_country or not self.game_map:
            return False, "Игра не начата"
        t = self.game_map.get_territory(sector_id)
        if not t:
            return False, "Сектор не найден"
        if t.owner == PLAYER_ID:
            return False, "Сектор уже ваш"
        if t.owner and t.owner in self.player_country.alliances:
            return False, "Нельзя захватывать союзные территории"
        if sector_id not in self.get_adjacent_sectors_to_player():
            return False, "Сектор не граничит с вашей территорией"
        if self.player_country.balance < CAPTURE_COST:
            return False, f"Нужно {CAPTURE_COST} денег (баланс: {self.player_country.balance})"
        if not self.player_country.has_resources_pack(CAPTURE_RESOURCES):
            missing = []
            for res, amount in CAPTURE_RESOURCES.items():
                if not self.player_country.has_resource(res, amount):
                    missing.append(f"{res}: {amount}")
            return False, f"Нужно ресурсов: {', '.join(missing)}"
        return True, ""

    def capture_sector(self, sector_id: int) -> tuple[bool, str]:
        ok, msg = self.can_capture_sector(sector_id)
        if not ok:
            return False, msg
        t = self.game_map.get_territory(sector_id)
        old_owner = t.owner
        if old_owner and old_owner in self.countries:
            self.countries[old_owner].remove_territory(sector_id, self.game_map)
        self.player_country.spend_resources(CAPTURE_COST)
        self.player_country.spend_resources_pack(CAPTURE_RESOURCES)
        self.player_country.add_territory(sector_id, self.game_map)
        return True, f"Сектор {sector_id} захвачен!"

    def get_adjacent_sectors_to_player(self):
        result = set()
        for tid in self.player_country.territories:
            result.update(self.get_adjacent_sectors(tid))
        return result - set(self.player_country.territories)

    def can_place_mine(self, sector_id: int) -> tuple[bool, str]:
        t = self.game_map.get_territory(sector_id) if self.game_map else None
        if not t or t.owner != PLAYER_ID:
            return False, "Сектор не принадлежит вам"
        biome = t.custom_data.get("biome", "") if t.custom_data else ""
        if biome not in MINE_BIOMES:
            return False, f"Шахту можно ставить только в {MINE_BIOMES}"
        if t.custom_data.get("building"):
            return False, "На секторе уже есть постройка"
        if self.player_country.balance < MINE_COST:
            return False, f"Нужно {MINE_COST} денег"
        if not self.player_country.has_resources_pack(MINE_BUILD_RESOURCES):
            return False, "Не хватает ресурсов для строительства шахты"
        return True, ""

    def can_place_bed(self, sector_id: int) -> tuple[bool, str]:
        t = self.game_map.get_territory(sector_id) if self.game_map else None
        if not t or t.owner != PLAYER_ID:
            return False, "Сектор не принадлежит вам"
        biome = t.custom_data.get("biome", "") if t.custom_data else ""
        if biome not in BED_BIOMES:
            return False, f"Грядки можно ставить только в {BED_BIOMES}"
        if t.custom_data.get("building"):
            return False, "На секторе уже есть постройка"
        if self.player_country.balance < BED_COST:
            return False, f"Нужно {BED_COST} денег"
        if not self.player_country.has_resources_pack(BED_BUILD_RESOURCES):
            return False, "Не хватает ресурсов для строительства грядок"
        return True, ""

    def place_mine(self, sector_id: int) -> tuple[bool, str]:
        ok, msg = self.can_place_mine(sector_id)
        if not ok:
            return False, msg
        t = self.game_map.get_territory(sector_id)
        self.player_country.balance -= MINE_COST
        self.player_country.spend_resources_pack(MINE_BUILD_RESOURCES)
        if not t.custom_data:
            t.custom_data = {}
        t.custom_data["building"] = "mine"
        return True, "Шахта построена!"

    def place_bed(self, sector_id: int) -> tuple[bool, str]:
        ok, msg = self.can_place_bed(sector_id)
        if not ok:
            return False, msg
        t = self.game_map.get_territory(sector_id)
        self.player_country.balance -= BED_COST
        self.player_country.spend_resources_pack(BED_BUILD_RESOURCES)
        if not t.custom_data:
            t.custom_data = {}
        t.custom_data["building"] = "bed"
        return True, "Грядки построены!"

    def can_place_sawmill(self, sector_id: int) -> tuple[bool, str]:
        t = self.game_map.get_territory(sector_id) if self.game_map else None
        if not t or t.owner != PLAYER_ID:
            return False, "Сектор не принадлежит вам"
        biome = t.custom_data.get("biome", "") if t.custom_data else ""
        if biome not in SAWMILL_BIOMES:
            return False, f"Лесопилку можно ставить только в {SAWMILL_BIOMES}"
        if t.custom_data.get("building"):
            return False, "На секторе уже есть постройка"
        if self.player_country.balance < SAWMILL_COST:
            return False, f"Нужно {SAWMILL_COST} денег"
        if not self.player_country.has_resources_pack(SAWMILL_BUILD_RESOURCES):
            return False, "Не хватает ресурсов для строительства лесопилки"
        return True, ""

    def place_sawmill(self, sector_id: int) -> tuple[bool, str]:
        ok, msg = self.can_place_sawmill(sector_id)
        if not ok:
            return False, msg
        t = self.game_map.get_territory(sector_id)
        self.player_country.balance -= SAWMILL_COST
        self.player_country.spend_resources_pack(SAWMILL_BUILD_RESOURCES)
        if not t.custom_data:
            t.custom_data = {}
        t.custom_data["building"] = "sawmill"
        return True, "Лесопилка построена!"

    def extract_from_sector(self, sector_id: int) -> tuple[bool, str]:
        t = self.game_map.get_territory(sector_id) if self.game_map else None
        if not t or t.owner != PLAYER_ID:
            return False, "Сектор не принадлежит вам"
        b = t.custom_data.get("building") if t.custom_data else None
        if not b:
            return False, "На секторе нет шахты или грядок"
        if b == "mine":
            gathered = []
            for res, (lo, hi) in MINE_PRODUCES.items():
                amt = random.randint(lo, hi)
                self.player_country.add_resource(res, amt)
                gathered.append(f"{res}:{amt}")
            return True, f"Добыто из шахты: {', '.join(gathered)}"
        if b == "bed":
            gathered = []
            for res, (lo, hi) in BED_PRODUCES.items():
                amt = random.randint(lo, hi)
                self.player_country.add_resource(res, amt)
                gathered.append(f"{res}:{amt}")
            return True, f"Собрано с грядок: {', '.join(gathered)}"
        if b == "sawmill":
            gathered = []
            for res, (lo, hi) in SAWMILL_PRODUCES.items():
                amt = random.randint(lo, hi)
                self.player_country.add_resource(res, amt)
                gathered.append(f"{res}:{amt}")
            return True, f"Добыто на лесопилке: {', '.join(gathered)}"
        return False, "Неизвестная постройка"

    def run_ai_turn(self):
        if not self.game_started or not self.game_map:
            return
        
        
        for cid, country in self.countries.items():
            if cid == PLAYER_ID:
                continue
            
            territory_income = len(country.territories) * 10  
            country.balance += territory_income
            
            
            self.apply_production_income(country)
            
        
        for cid, country in self.countries.items():
            if cid == PLAYER_ID:
                continue
            self._ai_act_for_country(country)

    def _ai_act_for_country(self, country: Country):
        if not country.territories:
            return

        
        self._ai_extract_resources(country)
        
       
        self._ai_build_structures(country)
        
        
        self._ai_expand_territory(country)
        
        
        self._ai_manage_diplomacy(country)

    def _ai_extract_resources(self, country: Country):
        for tid in country.territories:
            t = self.game_map.get_territory(tid)
            if not t or not t.custom_data:
                continue
                
            building = t.custom_data.get("building")
            if not building:
                continue
                
          
            if building == "mine":
                for res, (lo, hi) in MINE_PRODUCES.items():
                    amount = random.randint(lo, hi)
                    country.add_resource(res, amount)
            elif building == "bed":
                for res, (lo, hi) in BED_PRODUCES.items():
                    amount = random.randint(lo, hi)
                    country.add_resource(res, amount)
            elif building == "sawmill":
                for res, (lo, hi) in SAWMILL_PRODUCES.items():
                    amount = random.randint(lo, hi)
                    country.add_resource(res, amount)

    def _ai_build_structures(self, country: Country):
        territory_ids = list(country.territories)
        random.shuffle(territory_ids)
        
       
        priorities = [
            ("mine", MINE_BIOMES, MINE_COST, MINE_BUILD_RESOURCES),
            ("sawmill", SAWMILL_BIOMES, SAWMILL_COST, SAWMILL_BUILD_RESOURCES),
            ("bed", BED_BIOMES, BED_COST, BED_BUILD_RESOURCES)
        ]
        
        for building_type, biomes, cost, resources in priorities:
            for tid in territory_ids:
                t = self.game_map.get_territory(tid)
                if not t or (t.custom_data and t.custom_data.get("building")):
                    continue
                    
                biome = t.custom_data.get("biome", "") if t.custom_data else ""
                if biome in biomes and self._ai_can_build(country, building_type):
                    self._ai_build_on_sector(country, tid, building_type)
                    break 

    def _ai_expand_territory(self, country: Country):
        possible_targets = []
        for tid in country.territories:
            t = self.game_map.get_territory(tid)
            if not t:
                continue
            for nid in t.neighbors:
                nt = self.game_map.get_territory(nid)
                if not nt or nt.owner == country.id:
                    continue
                if nt.custom_data and nt.custom_data.get("biome") == "Море":
                    continue
                if nt.owner and nt.owner in country.alliances:
                    continue
                possible_targets.append(nid)

        
        neutral_targets = [tid for tid in possible_targets if not self.game_map.get_territory(tid).owner]
        enemy_targets = [tid for tid in possible_targets if self.game_map.get_territory(tid).owner]
        
        
        if country.balance >= CAPTURE_COST and country.has_resources_pack(CAPTURE_RESOURCES):
            target = None
            
          
            if neutral_targets and random.random() < 0.7:  
                target = random.choice(neutral_targets)
            elif enemy_targets:
                target = random.choice(enemy_targets)
                
            if target:
                self._ai_capture_sector(country, target)

    def _ai_manage_diplomacy(self, country: Country):
        if random.random() < 0.1:  
            other_countries = [cid for cid in self.countries.keys() if cid != country.id and cid != PLAYER_ID]
            if other_countries:
                target = random.choice(other_countries)
                
                if target in country.wars and random.random() < 0.3:  
                    country.wars.remove(target)
                    self.countries[target].wars.remove(country.id)
                elif target not in country.alliances and random.random() < 0.2: 
                    country.alliances.append(target)
                    self.countries[target].alliances.append(country.id)
                elif target not in country.wars and random.random() < 0.15:  
                    country.wars.append(target)
                    self.countries[target].wars.append(country.id)

    def _ai_can_build(self, country: Country, building_type: str) -> bool:
        if building_type == "mine":
            if country.balance < MINE_COST:
                return False
            return country.has_resources_pack(MINE_BUILD_RESOURCES)
        if building_type == "bed":
            if country.balance < BED_COST:
                return False
            return country.has_resources_pack(BED_BUILD_RESOURCES)
        if building_type == "sawmill":
            if country.balance < SAWMILL_COST:
                return False
            return country.has_resources_pack(SAWMILL_BUILD_RESOURCES)
        return False

    def _ai_build_on_sector(self, country: Country, sector_id: int, building_type: str):
        t = self.game_map.get_territory(sector_id)
        if not t:
            return
        if building_type == "mine":
            if not country.spend_resources_pack(MINE_BUILD_RESOURCES):
                return
            country.balance -= MINE_COST
        elif building_type == "bed":
            if not country.spend_resources_pack(BED_BUILD_RESOURCES):
                return
            country.balance -= BED_COST
        elif building_type == "sawmill":
            if not country.spend_resources_pack(SAWMILL_BUILD_RESOURCES):
                return
            country.balance -= SAWMILL_COST
        if not t.custom_data:
            t.custom_data = {}
        t.custom_data["building"] = building_type

    def _ai_capture_sector(self, country: Country, sector_id: int):
        t = self.game_map.get_territory(sector_id)
        if not t:
            return
        old_owner_id = t.owner
        if old_owner_id and old_owner_id in self.countries:
            old_owner = self.countries[old_owner_id]
            old_owner.remove_territory(sector_id, self.game_map)
        country.balance -= CAPTURE_COST
        country.spend_resources_pack(CAPTURE_RESOURCES)  
        country.add_territory(sector_id, self.game_map)
