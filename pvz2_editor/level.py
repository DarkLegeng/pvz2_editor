import json
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class PvZ2LevelEditor:
    def __init__(self):
        self.level_data = {
            "#comment": "Уровень создан с помощью Редактора уровней",
            "objects": [],
            "version": 1
        }
        self.current_aliases = {}
        self.available_stages = [
            "EgyptStage", "PirateStage", "WestStage", "IceageStage", 
            "LostCityStage", "FutureStage", "DarkStage", "EightiesStage",
            "DinoStage", "BeachStage", "ModernStage", "ZCorpStage", "RomanStage", "CarnivalStage"
        ]
        self.stage_mowers = {
            stage: f"{stage.replace('Stage', '')}Mowers" 
            for stage in self.available_stages
        }
        self.zombie_examples = [
            "tutorial", "tutorial_armor1", "tutorial_imp", "tutorial_gargantuar"
        ]
        self.plant_examples = [
            "sunflower", "peashooter", "wallnut"
        ]
        self.challenge_options = {
            1: ("save_mowers", "Не потерять газонокосилки", None, "RTID(SaveMowers@LevelModules)"),
            2: ("sun_used", "Ограничение на трату солнца", "max_sun_used", "RTID(SunUsed@.)"),
            3: ("sun_produced", "Произвести нужное количество солнц", "target_sun_produced", "RTID(SunProduced@.)"),
            4: ("sun_holdout", "Не тратить солнца в течении времени", "sun_holdout_seconds", "RTID(SunHoldout@.)"),
            5: ("plants_lost", "Ограничение на потерянные растения", "max_plants_lost", "RTID(PlantsLost@.)"),
            6: ("simultaneous_plants", "Ограничение на количество растений", "max_simultaneous_plants", "RTID(SimultaneousPlants@.)"),
            7: ("kill_zombies", "Убить зомби за время", ("zombies_to_kill", "kill_time"), "RTID(KillZombies@.)"),
            8: ("zombie_distance", "Не дать зомби пересечь линию", "zombie_distance", "RTID(ZombieDistance@.)"),
            9: ("level_timer", "Выжить в течении времени", "time_limit", "RTID(LevelTimer@CurrentLevel)")
        }
        self.zomboss_types = [
            "zombossmech_egypt", "zombossmech_pirate", "zombossmech_cowboy", "zombossmech_iceage",
            "zombossmech_lostcity", "zombossmech_future", "zombossmech_dark", "zombossmech_eighties", "zombossmech_dino",
            "zombossmech_beach", "zombossmech_roman", "zombossmech_circus"
        ]
        
    def create_new_level(self, name: str, description: str, level_number: int, 
                       stage: str, level_type: str,
                       last_stand_settings: Optional[Dict] = None,
                       conveyor_settings: Optional[Dict] = None,
                       challenges: Optional[Dict] = None,
                       level_properties: Optional[Dict] = None,
                       zomboss_settings: Optional[Dict] = None,
                       vasebreaker_settings: Optional[Dict] = None):
        if not self.is_alphanumeric(name) or not self.is_alphanumeric(description):
            raise ValueError("Название и описание должны содержать только английские буквы и цифры")
        
        modules = [
            "RTID(ZombiesDeadWinCon@LevelModules)",
            "RTID(DefaultZombieWinCondition@LevelModules)",
            "RTID(NewWaves@.)"
        ]
        
        if level_type == "conveyor":
            modules.append("RTID(ConveyorBelt@.)")
            if conveyor_settings:
                self._add_conveyor_belt(conveyor_settings["plants"])
        elif level_type == "vasebreaker":
            modules.append("RTID(VaseBreaker@.)")
            if vasebreaker_settings:
                self._add_vasebreaker(vasebreaker_settings)
        else:
            modules.append("RTID(SeedBank@.)")
            if last_stand_settings and last_stand_settings["enable"] and not (zomboss_settings and zomboss_settings.get("enable", False)):
                modules.append("RTID(LastStand@.)")
            
        if level_properties:
            if level_properties.get("enable_sun_bombs", False):
                level_properties["enable_sun_dropper"] = True
                
            if level_properties.get("enable_mowers", False) and stage in self.stage_mowers:
                modules.append(f"RTID({self.stage_mowers[stage]}@LevelModules)")
            if level_properties.get("enable_sun_dropper", False):
                modules.append("RTID(DefaultSunDropper@LevelModules)")
            if level_properties.get("enable_boosterama", False):
                modules.append("RTID(Boosterama@LevelModules)")
            if level_properties.get("enable_sun_bombs", False):
                modules.append("RTID(SunBombs@CurrentLevel)")
            if challenges:
                modules.append("RTID(ChallengeModule@.)")
            
            if level_properties.get("enable_invisighoul", False):
                modules.append("RTID(InvisiGhoul@CurrentLevel)")
            if level_properties.get("enable_column_minigame", False):
                modules.append("RTID(ColumnMinigame@CurrentLevel)")
            if level_properties.get("enable_all_jams", False):
                modules.append("RTID(EnableAllJams@CurrentLevel)")
        
        if zomboss_settings and zomboss_settings.get("enable", False):
            modules.append("RTID(ZombossBattle@.)")
            modules.append("RTID(ZombossIntro@LevelModules)")
            
        wave_manager_props = {
            "FlagWaveInterval": 1,
            "WaveCount": 0,
            "ZombieCountdownFirstWaveSecs": 1,
            "Waves": []
        }
        
        if level_properties and "suppress_flag_zombie" in level_properties:
            wave_manager_props["SuppressFlagZombie"] = level_properties["suppress_flag_zombie"]
            
        level_definition = {
            "objclass": "LevelDefinition",
            "objdata": {
                "StageModule": f"RTID({stage}@LevelModules)",
                "Name": name,
                "Description": description,
                "LevelNumber": level_number,
                "Loot": "RTID(NoLoot@LevelModules)",
                "Modules": modules
            }
        }
        
        if level_type != "vasebreaker" and not (last_stand_settings and last_stand_settings["enable"]):
            level_definition["objdata"]["StartingSun"] = 50
        
        if level_type == "vasebreaker":
            level_definition["objdata"]["IsVasebreaker"] = True
            
        if level_properties:
            for prop in ["zombie_level", "grid_item_level", "fixed_plant_level"]:
                if prop in level_properties:
                    level_definition["objdata"][prop.capitalize()] = level_properties[prop]
            if "suppress_plantfood_purchase" in level_properties:
                level_definition["objdata"]["SuppressPlantfoodPurchase"] = level_properties["suppress_plantfood_purchase"]
                
        self.level_data["objects"] = [
            level_definition,
            {
                "aliases": ["NewWaves"],
                "objclass": "WaveManagerModuleProperties",
                "objdata": {"WaveManagerProps": "RTID(WaveManagerProps@.)"}
            },
            {
                "aliases": ["WaveManagerProps"],
                "objclass": "WaveManagerProperties",
                "objdata": wave_manager_props
            }
        ]
        
        if level_type == "conveyor":
            self.level_data["objects"].append({
                "aliases": ["ConveyorBelt"],
                "objclass": "ConveyorSeedBankProperties",
                "objdata": {
                    "DropDelayConditions": [
                        {"Delay": 3, "MaxPackets": 0},
                        {"Delay": 6, "MaxPackets": 2},
                        {"Delay": 9, "MaxPackets": 4},
                        {"Delay": 12, "MaxPackets": 8}
                    ],
                    "InitialPlantList": conveyor_settings["plants"],
                    "SpeedConditions": [{"MaxPackets": 0, "Speed": 100}]
                }
            })
        elif level_type == "vasebreaker":
            pass
        else:
            seed_bank_props = {
                "aliases": ["SeedBank"],
                "objclass": "SeedBankProperties",
                "objdata": {"SelectionMethod": "chooser"}
            }
            for prop in ["seed_slots_count", "preset_plants", "excluded_plants", "included_plants"]:
                if level_properties and prop in level_properties:
                    if prop == "preset_plants":
                        seed_bank_props["objdata"]["PresetPlantList"] = [{"PlantType": plant} for plant in level_properties["preset_plants"]]
                    else:
                        seed_bank_props["objdata"][prop.capitalize()] = level_properties[prop]
            self.level_data["objects"].append(seed_bank_props)
        
        if level_properties:
            for module, prop_class in [
                ("enable_invisighoul", "InvisighoulMinigameProperties"),
                ("enable_column_minigame", "ColumnMinigameProperties"),
                ("enable_all_jams", "JamZombiesModuleProperties")
            ]:
                if level_properties.get(module, False):
                    self.level_data["objects"].append({
                        "aliases": [module.replace("enable_", "").capitalize()],
                        "objclass": prop_class,
                        "objdata": {}
                    })
        
        if challenges:
            self._add_challenges(challenges)
            
        if last_stand_settings and last_stand_settings["enable"] and not (zomboss_settings and zomboss_settings.get("enable", False)):
            self.level_data["objects"].append({
                "aliases": ["LastStand"],
                "objclass": "LastStandMinigameProperties",
                "objdata": {
                    "StartingPlantfood": last_stand_settings["plantfood"],
                    "StartingSun": last_stand_settings["sun"]
                }
            })
            
        if zomboss_settings and zomboss_settings.get("enable", False):
            self._add_zomboss(zomboss_settings)
            
        if level_type == "vasebreaker" and vasebreaker_settings:
            self._add_vasebreaker(vasebreaker_settings)
            
        if level_properties and level_properties.get("enable_sun_bombs", False):
            self._add_sun_bombs()
            
        self._update_current_aliases()
    
    def _add_sun_bombs(self):
        sun_bomb_props = {
            "aliases": ["SunBombs"],
            "objclass": "SunBombChallengeProperties",
            "objdata": {
                "PlantBombExplosionRadius": 25,
                "PlantDamage": 1000,
                "ZombieBombExplosionRadius": 80,
                "ZombieDamage": 500
            }
        }
        self.level_data["objects"].append(sun_bomb_props)
    
    def _add_vasebreaker(self, settings: Dict):
        vasebreaker_props = {
            "aliases": ["VaseBreaker"],
            "objclass": "VaseBreakerPresetProperties",
            "objdata": {
                "MinColumnIndex": settings["MinColumnIndex"],
                "MaxColumnIndex": settings["MaxColumnIndex"],
                "Vases": settings["Vases"],
                "NumColoredPlantVases": settings["NumColoredPlantVases"],
                "NumColoredZombieVases": settings["NumColoredZombieVases"]
            }
        }
        self.level_data["objects"].append(vasebreaker_props)
    
    def _add_zomboss(self, settings: Dict):
        zomboss_props = {
            "aliases": ["ZombossBattle"],
            "objclass": "ZombossBattleModuleProperties",
            "objdata": {
                "ReservedColumnCount": 2,
                "ZombossMechType": settings["mech_type"],
                "ZombossDeathRow": 3,
                "ZombossDeathColumn": 5,
                "ZombossSpawnGridPosition": {
                    "mX": 6,
                    "mY": 3
                }
            }
        }
        self.level_data["objects"].append(zomboss_props)
        
    def _add_conveyor_belt(self, plants: List[Dict]):
        conveyor_props = {
            "aliases": ["ConveyorBelt"],
            "objclass": "ConveyorSeedBankProperties",
            "objdata": {
                "DropDelayConditions": [
                    {"Delay": 3, "MaxPackets": 0},
                    {"Delay": 6, "MaxPackets": 2},
                    {"Delay": 9, "MaxPackets": 4},
                    {"Delay": 12, "MaxPackets": 8}
                ],
                "InitialPlantList": plants,
                "SpeedConditions": [{"MaxPackets": 0, "Speed": 100}]
            }
        }
        self.level_data["objects"].append(conveyor_props)
        
    def _add_challenges(self, challenges: Dict[str, Any]):
        challenge_list = []
        
        for num, (key, _, _, rtid) in self.challenge_options.items():
            if challenges.get(key, False):
                challenge_list.append(rtid)
        
        if not challenge_list:
            return
            
        challenge_module = {
            "aliases": ["ChallengeModule"],
            "objclass": "StarChallengeModuleProperties",
            "objdata": {
                "Challenges": [challenge_list],
                "ChallengesAlwaysAvailable": True
            }
        }
        self.level_data["objects"].append(challenge_module)
        
        for num, (key, _, param_key, _) in self.challenge_options.items():
            if not challenges.get(key, False) or key == "save_mowers":
                continue
                
            if key == "sun_used":
                self.level_data["objects"].append({
                    "aliases": ["SunUsed"],
                    "objclass": "StarChallengeSunUsedProps",
                    "objdata": {"MaximumSun": challenges.get("max_sun_used", 500)}
                })
            elif key == "sun_produced":
                self.level_data["objects"].append({
                    "aliases": ["SunProduced"],
                    "objclass": "StarChallengeSunProducedProps",
                    "objdata": {"TargetSun": challenges.get("target_sun_produced", 1000)}
                })
            elif key == "sun_holdout":
                self.level_data["objects"].append({
                    "aliases": ["SunHoldout"],
                    "objclass": "StarChallengeSpendSunHoldoutProps",
                    "objdata": {"HoldoutSeconds": challenges.get("sun_holdout_seconds", 60)}
                })
            elif key == "plants_lost":
                self.level_data["objects"].append({
                    "aliases": ["PlantsLost"],
                    "objclass": "StarChallengePlantsLostProps",
                    "objdata": {"MaximumPlantsLost": challenges.get("max_plants_lost", 5)}
                })
            elif key == "simultaneous_plants":
                self.level_data["objects"].append({
                    "aliases": ["SimultaneousPlants"],
                    "objclass": "StarChallengeSimultaneousPlantsProps",
                    "objdata": {"MaximumPlants": challenges.get("max_simultaneous_plants", 10)}
                })
            elif key == "kill_zombies":
                self.level_data["objects"].append({
                    "aliases": ["KillZombies"],
                    "objclass": "StarChallengeKillZombiesInTimeProps",
                    "objdata": {
                        "ZombiesToKill": challenges.get("zombies_to_kill", 10),
                        "Time": challenges.get("kill_time", 30)
                    }
                })
            elif key == "zombie_distance":
                self.level_data["objects"].append({
                    "aliases": ["ZombieDistance"],
                    "objclass": "StarChallengeZombieDistanceProps",
                    "objdata": {"TargetDistance": challenges.get("zombie_distance", 1)}
                })
            elif key == "level_timer":
                self.level_data["objects"].append({
                    "aliases": ["LevelTimer"],
                    "objclass": "StarChallengeLevelTimerProperties",
                    "objdata": {"TimeLimit": challenges.get("time_limit", 300)}
                })
        
    def is_alphanumeric(self, text: str) -> bool:
        return bool(re.match('^[a-zA-Z0-9 _.!?-]+$', text))
        
    def set_wave_properties(self, flag_wave_interval: int, wave_count: int, first_wave_delay: int):
        wave_props = self.current_aliases.get("WaveManagerProps")
        if wave_props:
            wave_props["objdata"].update({
                "FlagWaveInterval": max(1, flag_wave_interval) if wave_count > 0 else 1,
                "WaveCount": wave_count,
                "ZombieCountdownFirstWaveSecs": max(1, first_wave_delay) if wave_count > 0 else 1
            })
            
    def add_wave(self, zombie_types: List[str], counts: Optional[List[int]] = None, plantfood_zombies: int = 0):
        if not all(self.is_alphanumeric(z) for z in zombie_types):
            raise ValueError("Типы зомби должны содержать только английские буквы и цифры")
            
        wave_id = f"w{len([obj for obj in self.level_data['objects'] if 'aliases' in obj and obj['aliases'][0].startswith('w')])}zombies"
        
        zombies = []
        if counts:
            zombies = [
                {"Type": f"RTID({z_type}@ZombieTypes)"} 
                for z_type, count in zip(zombie_types, counts) 
                for _ in range(count)
            ]
        else:
            zombies = [{"Type": f"RTID({z_type}@ZombieTypes)"} for z_type in zombie_types]
        
        wave_data = {
            "aliases": [wave_id],
            "objclass": "SpawnZombiesJitteredWaveActionProps",
            "objdata": {"Zombies": zombies}
        }
        
        if plantfood_zombies > 0:
            total_zombies = sum(counts) if counts else len(zombie_types)
            if plantfood_zombies > total_zombies:
                plantfood_zombies = total_zombies
            wave_data["objdata"]["AdditionalPlantfood"] = plantfood_zombies
        
        self.level_data["objects"].append(wave_data)
        
        wave_props = self.current_aliases.get("WaveManagerProps")
        if wave_props:
            wave_props["objdata"]["Waves"].append([f"RTID({wave_id}@.)"])
            wave_props["objdata"]["WaveCount"] = len(wave_props["objdata"]["Waves"])
            
        self._update_current_aliases()
        
    def set_rewards(self, reward_type: Optional[str], reward_param: Optional[str]):
        level_def = self._find_object_by_class("LevelDefinition")
        if not level_def:
            return
            
        reward_fields = {
            "FirstRewardType": reward_type,
            "FirstRewardParam": reward_param,
            "ReplayRewardType": reward_type,
            "ReplayRewardParam": reward_param
        }
        
        for field, value in reward_fields.items():
            if value:
                level_def["objdata"][field] = value
            else:
                level_def["objdata"].pop(field, None)
            
    def save_level(self, file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.level_data, f, indent=2, ensure_ascii=False)
            
    def _update_current_aliases(self):
        self.current_aliases = {
            alias: obj 
            for obj in self.level_data["objects"] 
            if "aliases" in obj 
            for alias in obj["aliases"]
        }
                    
    def _find_object_by_class(self, objclass: str) -> Optional[Dict]:
        return next((obj for obj in self.level_data["objects"] if obj["objclass"] == objclass), None)

class VasebreakerGridEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Редактор Вазобоя - Выделение столбцов")
        self.rows = 5
        self.cols = 9
        self.cell_size = 60
        self.current_color = '#aaffaa'
        self.normal_color = '#f0f0f0'
        self.label_width = 40
        self.header_height = 30
        self.result = None
        self.vase_types = []
        self.setup_ui()
        self.create_grid()
        self.bind_events()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        x_header_frame = ttk.Frame(main_frame, height=self.header_height)
        x_header_frame.pack(fill=tk.X)
        ttk.Label(x_header_frame, width=self.label_width//7).pack(side=tk.LEFT)
        
        for x in range(self.cols):
            col_frame = ttk.Frame(x_header_frame)
            col_frame.pack(side=tk.LEFT, padx=2)
            btn = ttk.Button(col_frame, text="Выбрать", width=6, command=lambda x=x: self.toggle_column_color(x))
            btn.pack(side=tk.TOP)
            ttk.Label(col_frame, text=f"Столбец {x}", width=8, anchor="center").pack(side=tk.TOP)
        
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            grid_frame,
            width=self.cols*self.cell_size + self.label_width,
            height=self.rows*self.cell_size,
            bg='white',
            highlightthickness=0
        )
        
        hscroll = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.canvas.xview)
        vscroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        
        self.canvas.grid(row=0, column=1, sticky="nsew")
        vscroll.grid(row=0, column=2, sticky="ns")
        hscroll.grid(row=1, column=1, sticky="ew")
        
        y_label_frame = ttk.Frame(grid_frame, width=self.label_width)
        y_label_frame.grid(row=0, column=0, sticky="ns")
        
        for y in range(self.rows):
            frame = ttk.Frame(y_label_frame)
            frame.pack(fill=tk.X, pady=(0, self.cell_size-20))
            btn = ttk.Button(frame, text="Выбрать", width=6, command=lambda y=y: self.toggle_row_color(y))
            btn.pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text=f"Ряд {y}", anchor="e", width=5).pack(side=tk.LEFT)
        
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        
        self.status = ttk.Label(main_frame, text="Выделено столбцов: 0 | Для Вазобоя выделяйте только столбцы (Y)")
        self.status.pack(fill=tk.X)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=5)
        
        for text, cmd in [
            ("Сбросить всё", self.reset_grid),
            ("Выделить всё", lambda: self.select_all(self.current_color)),
            ("Настроить вазы", self.setup_vases),
            ("Сохранить", self.save_data),
            ("Отмена", self.cancel)
        ]:
            ttk.Button(button_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)
    
    def create_grid(self):
        self.grid = {}
        for y in range(self.rows):
            for x in range(self.cols):
                x1 = x * self.cell_size + self.label_width
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=self.normal_color,
                    outline='black',
                    tags=(f"cell_{y}_{x}", "cell")
                )
                self.grid[(y, x)] = {'id': rect, 'marked': False, 'color': None}
    
    def bind_events(self):
        self.canvas.tag_bind("cell", "<Button-1>", self.toggle_cell)
        self.canvas.bind("<Motion>", self.show_coordinates)
    
    def toggle_cell(self, event):
        x = int(self.canvas.canvasx(event.x) - self.label_width) // self.cell_size
        y = int(self.canvas.canvasy(event.y) // self.cell_size)
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.toggle_column_color(x)
    
    def show_coordinates(self, event):
        x = int(self.canvas.canvasx(event.x) - self.label_width) // self.cell_size
        y = int(self.canvas.canvasy(event.y) // self.cell_size)
        if 0 <= x < self.cols and 0 <= y < self.rows:
            marked_columns = len(self.get_marked_columns())
            self.status.config(
                text=f"Выделено столбцов: {marked_columns} | Для Vasebreaker выделяйте только столбцы (X) | Позиция: Ряд {y}, Столбец {x}"
            )
    
    def get_marked_columns(self):
        marked_columns = set()
        for (y, x), cell in self.grid.items():
            if cell['marked']:
                marked_columns.add(x)
        return sorted(marked_columns)
    
    def get_total_vases(self):
        marked_columns = self.get_marked_columns()
        if not marked_columns:
            return 0
        min_col = min(marked_columns)
        max_col = max(marked_columns)
        return (max_col - min_col + 1) * self.rows
    
    def update_status(self):
        marked_columns = len(self.get_marked_columns())
        total_vases = self.get_total_vases()
        self.status.config(text=f"Выделено столбцов: {marked_columns} | Всего ваз: {total_vases} | Для Vasebreaker выделяйте только столбцы (X)")
    
    def reset_grid(self):
        for cell in self.grid.values():
            cell['marked'] = False
            cell['color'] = None
            self.canvas.itemconfig(cell['id'], fill=self.normal_color)
        self.update_status()
    
    def select_all(self, color):
        for cell in self.grid.values():
            cell['marked'] = True
            cell['color'] = color
            self.canvas.itemconfig(cell['id'], fill=color)
        self.update_status()
    
    def toggle_row_color(self, row):
        all_marked = all(self.grid[(row, x)]['marked'] for x in range(self.cols))
        for x in range(self.cols):
            cell = self.grid[(row, x)]
            if all_marked:
                cell['marked'] = False
                cell['color'] = None
                self.canvas.itemconfig(cell['id'], fill=self.normal_color)
            else:
                cell['marked'] = True
                cell['color'] = self.current_color
                self.canvas.itemconfig(cell['id'], fill=self.current_color)
        self.update_status()
    
    def toggle_column_color(self, column):
        all_marked = all(self.grid[(y, column)]['marked'] for y in range(self.rows))
        for y in range(self.rows):
            cell = self.grid[(y, column)]
            if all_marked:
                cell['marked'] = False
                cell['color'] = None
                self.canvas.itemconfig(cell['id'], fill=self.normal_color)
            else:
                cell['marked'] = True
                cell['color'] = self.current_color
                self.canvas.itemconfig(cell['id'], fill=self.current_color)
        self.update_status()
    
    def setup_vases(self):
        total_vases = self.get_total_vases()
        if total_vases == 0:
            messagebox.showwarning("Предупреждение", "Сначала выделите столбцы!")
            return
        
        self.vase_types = []
        vase_window = tk.Toplevel(self.master)
        vase_window.title("Настройка содержимого ваз")
        
        window_width = 600
        window_height = 400
        screen_width = vase_window.winfo_screenwidth()
        screen_height = vase_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        vase_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        main_frame = ttk.Frame(vase_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text=f"Всего ваз для настройки: {total_vases}", font=('Arial', 10, 'bold')).pack(pady=5)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.vase_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.vase_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.vase_listbox.yview)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        for text, cmd in [
            ("Добавить вазу с растением", lambda: self.add_vase_type(vase_window, "plant")),
            ("Добавить вазу с зомби", lambda: self.add_vase_type(vase_window, "zombie")),
            ("Добавить вазу с удобрением", lambda: self.add_vase_type(vase_window, "collectable")),
            ("Удалить выбранное", self.remove_vase_type),
            ("Готово", vase_window.destroy)
        ]:
            ttk.Button(button_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5, expand=True)
        
        self.update_vase_listbox()
    
    def add_vase_type(self, parent, vase_type):
        if vase_type == "plant":
            plant = simpledialog.askstring("Тип растения", "Введите тип растения (например: peashooter, wallnut):", parent=parent)
            if plant and re.match('^[a-z0-9_]+$', plant):
                count = simpledialog.askinteger("Количество", "Введите количество таких ваз:", parent=parent, minvalue=1)
                if count:
                    self.vase_types.append({"PlantTypeName": plant, "Count": count})
        elif vase_type == "zombie":
            zombie = simpledialog.askstring("Тип зомби", "Введите тип зомби (например: tutorial, tutorial_armor1):", parent=parent)
            if zombie and re.match('^[a-z0-9_]+$', zombie):
                count = simpledialog.askinteger("Количество", "Введите количество таких ваз:", parent=parent, minvalue=1)
                if count:
                    self.vase_types.append({"ZombieTypeName": zombie, "Count": count})
        elif vase_type == "collectable":
            count = simpledialog.askinteger("Количество", "Введите количество ваз с удобрением:", parent=parent, minvalue=1)
            if count:
                self.vase_types.append({"CollectableTypeName": "plantfood", "Count": count})
        self.update_vase_listbox()
    
    def remove_vase_type(self):
        selection = self.vase_listbox.curselection()
        if selection:
            self.vase_types.pop(selection[0])
            self.update_vase_listbox()
    
    def update_vase_listbox(self):
        self.vase_listbox.delete(0, tk.END)
        total_count = 0
        
        for vase in self.vase_types:
            if "PlantTypeName" in vase:
                self.vase_listbox.insert(tk.END, f"Растение: {vase['PlantTypeName']} x{vase['Count']}")
            elif "ZombieTypeName" in vase:
                self.vase_listbox.insert(tk.END, f"Зомби: {vase['ZombieTypeName']} x{vase['Count']}")
            elif "CollectableTypeName" in vase:
                self.vase_listbox.insert(tk.END, f"Удобрение: {vase['CollectableTypeName']} x{vase['Count']}")
            total_count += vase['Count']
        
        self.vase_listbox.insert(tk.END, f"=== Всего: {total_count} ваз ===")
    
    def save_data(self):
        marked_columns = self.get_marked_columns()
        if not marked_columns:
            messagebox.showwarning("Предупреждение", "Не выделено ни одного столбца!")
            return
        
        total_vases = self.get_total_vases()
        total_configured = sum(vase['Count'] for vase in self.vase_types)
        
        if total_configured != total_vases:
            messagebox.showwarning("Ошибка", f"Количество ваз не совпадает! Нужно настроить {total_vases} ваз, а настроено {total_configured}.")
            return
        
        if not self.vase_types:
            messagebox.showwarning("Ошибка", "Не настроено ни одной вазы!")
            return
        
        colored_plants = sum(v['Count'] for v in self.vase_types if 'PlantTypeName' in v)
        colored_zombies = sum(v['Count'] for v in self.vase_types if 'ZombieTypeName' in v)
        
        self.result = {
            "MinColumnIndex": min(marked_columns),
            "MaxColumnIndex": max(marked_columns),
            "Vases": self.vase_types,
            "NumColoredPlantVases": colored_plants,
            "NumColoredZombieVases": colored_zombies
        }
        self.master.destroy()
    
    def cancel(self):
        self.result = None
        self.master.destroy()

def get_vasebreaker_settings() -> Dict[str, Any]:
    root = tk.Tk()
    root.withdraw()
    editor_window = tk.Toplevel(root)
    editor_window.title("Настройка Vasebreaker")
    
    window_width = 850
    window_height = 550
    screen_width = editor_window.winfo_screenwidth()
    screen_height = editor_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    editor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    editor = VasebreakerGridEditor(editor_window)
    editor_window.wait_window(editor_window)
    return editor.result

def get_alphanumeric_input(prompt: str) -> str:
    while True:
        text = input(prompt).strip()
        if re.match('^[a-zA-Z0-9 _.!?-]+$', text):
            return text
        print("Ошибка: Допустимы только английские буквы и цифры")

def get_valid_integer(prompt: str, min_val: int = None, max_val: int = None) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            if (min_val is None or value >= min_val) and (max_val is None or value <= max_val):
                return value
            error_msg = f"Ошибка: Значение должно быть между {min_val} и {max_val}" if min_val is not None and max_val is not None else \
                       f"Ошибка: Значение должно быть не меньше {min_val}" if min_val is not None else \
                       f"Ошибка: Значение должно быть не больше {max_val}"
            print(error_msg)
        except ValueError:
            print("Ошибка: Пожалуйста, введите целое число")

def select_from_list(options: List[Tuple[str, str]], title: str) -> str:
    print(f"\n{title}:")
    print("0. Ввести свой вариант вручную")
    for i, (num, name) in enumerate(options, 1):
        print(f"{i}. {name}")
    
    while True:
        choice = input(f"Выберите номер (0 для ручного ввода): ").strip()
        if choice == "0":
            custom = get_alphanumeric_input("Введите значение: ")
            if custom:
                return custom
            print("Ошибка: Значение не может быть пустым")
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return options[choice_num-1][1]
            print(f"Пожалуйста, введите число от 0 до {len(options)}")
        except ValueError:
            print("Ошибка: Введите номер")

def get_yes_no_input(prompt: str) -> bool:
    while True:
        choice = input(prompt + " (1 - да, 0 - нет): ").strip()
        if choice == "1":
            return True
        if choice == "0":
            return False
        print("Ошибка: Пожалуйста, введите 1 или 0")

def get_multiple_choice(options: List[Tuple[str, str]], title: str) -> Dict[str, bool]:
    print(f"\n{title}:")
    print("0. Не добавлять ничего")
    for i, (key, name) in enumerate(options, 1):
        print(f"{i}. {name}")
    
    print("\nВведите номера нужных опций через запятую")
    print("Или 0 чтобы пропустить этот шаг")
    
    selected = {}
    while True:
        choice = input("Ваш выбор: ").strip()
        if choice == "0":
            return {}
        
        try:
            choices = {int(num.strip()) for num in choice.split(',') if num.strip()}
            invalid = choices - set(range(1, len(options)+1))
            if invalid:
                print(f"Ошибка: Номера {invalid} не существуют")
                continue
            
            for num in choices:
                selected[options[num-1][0]] = True
            return selected
            
        except ValueError:
            print("Ошибка: Пожалуйста, введите номера через запятую")

def get_zombie_wave_settings(wave_num: int, editor) -> Tuple[List[str], Optional[List[int]], int]:
    print(f"\n=== Настройка волны {wave_num + 1} ===")
    print("Доступные типы зомби (вводите через запятую):")
    print("Примеры: " + ", ".join(editor.zombie_examples))
    
    while True:
        zombies = input("Введите типы зомби: ").strip().lower()
        if zombies:
            zombies = [z.strip() for z in zombies.split(',') if z.strip()]
            if not all(re.match('^[a-z0-9_]+$', z) for z in zombies):
                print("Ошибка: Названия зомби должны содержать только английские буквы и цифры")
                continue
            break
        print("Ошибка: Пожалуйста, введите хотя бы один тип зомби")
    
    print("\nВведите количество для каждого типа зомби (через запятую)")
    print("Оставьте пустым для значения по умолчанию (1 каждого типа)")
    counts = None
    while True:
        counts_str = input("Количества: ").strip()
        if not counts_str:
            break
        
        try:
            counts = [int(c.strip()) for c in counts_str.split(',')]
            if len(counts) != len(zombies):
                print(f"Ошибка: Нужно ввести {len(zombies)} значений")
                continue
            if any(c <= 0 for c in counts):
                print("Ошибка: Все значения должны быть больше 0")
                continue
            break
        except ValueError:
            print("Ошибка: Пожалуйста, введите числа через запятую")
    
    total_zombies = sum(counts) if counts else len(zombies)
    plantfood_zombies = 0
    if total_zombies > 0:
        print(f"\nКоличество зомби в волне: {total_zombies}")
        plantfood_zombies = get_valid_integer(
            "Сколько зомби должны иметь удобрение? (0 - не добавлять): ",
            0, total_zombies
        )
    
    return zombies, counts, plantfood_zombies

def get_plant_reward() -> Optional[str]:
    print("\nДоступные растения для награды:")
    print("Введите название растения или 0 чтобы не добавлять награду")
    print("Примеры: sunflower, peashooter, wallnut")
    while True:
        plant = input("Введите растение для награды (или 0): ").strip().lower()
        if plant == "0":
            return None
        if plant and re.match('^[a-z0-9]+$', plant):
            return plant
        print("Ошибка: Пожалуйста, введите корректное название растения или 0")

def get_last_stand_settings() -> Dict[str, Any]:
    print("\n=== Настройки режима Last Stand ===")
    return {
        "enable": True,
        "sun": get_valid_integer("Стартовое количество солнца: "),
        "plantfood": get_valid_integer("Стартовое удобрение (0-5): ", 0, 5)
    }

def get_conveyor_settings(editor) -> Dict[str, Any]:
    print("\n=== Настройка конвейера ===")
    print("Доступные растения (вводите через запятую):")
    print("Примеры: " + ", ".join(editor.plant_examples))
    
    plants = []
    while True:
        plant_types = input("Введите типы растений через запятую: ").strip().lower()
        if not plant_types:
            print("Ошибка: Пожалуйста, введите хотя бы одно растение")
            continue
            
        plant_types = [p.strip() for p in plant_types.split(',') if p.strip()]
        if not all(re.match('^[a-z0-9]+$', p) for p in plant_types):
            print("Ошибка: Названия растений должны содержать только английские буквы и цифры")
            continue
            
        for plant in plant_types:
            print(f"\nНастройка растения: {plant}")
            min_count = get_valid_integer("Минимальное количество: ", 1)
            max_count = get_valid_integer(f"Максимальное количество ({min_count}): ", min_count)
            
            plants.append({
                "MinCount": min_count,
                "MaxCount": max_count,
                "MinWeightFactor": 2,
                "MaxWeightFactor": 0,
                "Weight": 15,
                "PlantType": plant
            })
        
        return {"plants": plants}

def get_zomboss_settings(editor) -> Dict[str, Any]:
    print("\n=== Настройки Зомбосса ===")
    settings = {"enable": False}
    
    print("\nВыберите Зомбосса:")
    print("0. Не добавлять Зомбосса")
    for i, ztype in enumerate(editor.zomboss_types, 1):
        print(f"{i}. {ztype}")
    
    while True:
        choice = input(f"Выберите тип (0-{len(editor.zomboss_types)}): ").strip()
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return settings
            if 1 <= choice_num <= len(editor.zomboss_types):
                settings["enable"] = True
                settings["mech_type"] = editor.zomboss_types[choice_num-1]
                return settings
            print(f"Пожалуйста, введите число от 0 до {len(editor.zomboss_types)}")
        except ValueError:
            print("Ошибка: Введите номер")

def get_level_properties(editor) -> Dict[str, Any]:
    properties = {}
    
    settings_options = [
        ("suppress_plantfood_purchase", "Запретить покупку удобрений"),
        ("suppress_flag_zombie", "Отключить флаг-зомби"),
        ("enable_mowers", "Добавить газонокосилки"),
        ("enable_sun_dropper", "Включить периодическое выпадение солнца"),
        ("enable_boosterama", "Включить режим все растения с удобрением"),
        ("enable_sun_bombs", "Включить солнечные бомбы"),
        ("enable_invisighoul", "Сделать всех зомби невидимыми"),
        ("enable_column_minigame", "Добавить высадку по 5 дорожкам "),
        ("enable_all_jams", "Добавить музыку для зомби")
    ]
    selected_settings = get_multiple_choice(settings_options, "Дополнительные настройки уровня")
    properties.update(selected_settings)
    
    level_options = [
        ("zombie_level", "Установить уровень зомби"),
        ("grid_item_level", "Установить уровень предметам"),
        ("fixed_plant_level", "Установить уровень растениям"),
        ("seed_slots_count", "Ограничить количество слотов для растений"),
        ("preset_plants", "Добавить обязательные растения"),
        ("excluded_plants", "Добавить запрещённые растения"),
        ("included_plants", "Добавить разрешённые растения")
    ]
    selected_level_props = get_multiple_choice(level_options, "Настраиваемые свойства уровня")
    
    for prop in selected_level_props:
        if prop in ["preset_plants", "excluded_plants", "included_plants"]:
            print(f"\n=== {'Обязательные' if prop == 'preset_plants' else 'Запрещённые' if prop == 'excluded_plants' else 'Разрешённые'} растения ===")
            print("Введите растения через запятую или 0 чтобы отменить")
            print("Примеры: " + ", ".join(editor.plant_examples))
            while True:
                plants = input("Растения: ").strip().lower()
                if plants == "0":
                    break
                plants = [p.strip() for p in plants.split(',') if p.strip()]
                if plants and all(re.match('^[a-z0-9]+$', p) for p in plants):
                    properties[prop] = plants
                    break
                print("Ошибка: Введите корректные названия растений через запятую")
        else:
            properties[prop] = get_valid_integer(f"Введите значение для {level_options[[x[0] for x in level_options].index(prop)][1]}: ", 1)
    
    return properties

def get_challenge_settings() -> Dict[str, Any]:
    editor = PvZ2LevelEditor()
    challenges = {}
    challenge_options = [(key, name) for num, (key, name, _, _) in editor.challenge_options.items()]
    selected_challenges = get_multiple_choice(challenge_options, "Выбор челленджей")
    
    for challenge in selected_challenges:
        if challenge == "sun_used":
            challenges["max_sun_used"] = get_valid_integer("Максимальное количество солнца для траты: ")
        elif challenge == "sun_produced":
            challenges["target_sun_produced"] = get_valid_integer("Произвести нужное количество солнца: ")
        elif challenge == "sun_holdout":
            challenges["sun_holdout_seconds"] = get_valid_integer("Не тратить солнца в течении времени (секунды): ")
        elif challenge == "plants_lost":
            challenges["max_plants_lost"] = get_valid_integer("Максимальное количество потерянных растений: ")
        elif challenge == "simultaneous_plants":
            challenges["max_simultaneous_plants"] = get_valid_integer("Максимальное количество растений: ")
        elif challenge == "kill_zombies":
            challenges["zombies_to_kill"] = get_valid_integer("Количество зомби для убийства: ")
            challenges["kill_time"] = get_valid_integer("Время для выполнения (секунды): ")
        elif challenge == "zombie_distance":
            challenges["zombie_distance"] = get_valid_integer("Максимальное расстояние линии (1-8): ", 1, 8)
        elif challenge == "level_timer":
            challenges["time_limit"] = get_valid_integer("Продержитесь в течении (секунды): ")
    
    challenges.update(selected_challenges)
    return challenges

def main():
    print("=== PvZ 2 Level Creator ===")
    print("Следуйте инструкциям для создания своего уровня")
    
    editor = PvZ2LevelEditor()
    
    print("\n=== Выбор типа уровня ===")
    print("1. Стандартный (выбор растений) (+Last Stand или +Зомбосс)")
    print("2. Конвейер (+Зомбосс)")
    print("3. Вазобой")
    level_type = ""
    while True:
        choice = input("Выберите тип уровня (1-3): ").strip()
        if choice == "1":
            level_type = "seedbank"
            break
        elif choice == "2":
            level_type = "conveyor"
            break
        elif choice == "3":
            level_type = "vasebreaker"
            break
        print("Ошибка: Пожалуйста, введите 1, 2 или 3")
    
    last_stand_settings = None
    zomboss_settings = {"enable": False}
    vasebreaker_settings = None
    
    if level_type == "seedbank":
        print("\n=== Выбор дополнительного типа ===")
        print("0. Не добавлять ничего")
        print("1. Добавить Зомбосса")
        print("2. Добавить Last Stand")
        
        while True:
            boss_choice = input("Выберите режим (0-2): ").strip()
            if boss_choice == "0":
                break
            elif boss_choice == "1":
                zomboss_settings = get_zomboss_settings(editor)
                break
            elif boss_choice == "2":
                last_stand_settings = get_last_stand_settings()
                break
            print("Ошибка: Пожалуйста, введите 0, 1 или 2")
    elif level_type == "conveyor":
        zomboss_settings = get_zomboss_settings(editor)
    elif level_type == "vasebreaker":
        print("\n=== Настройка Вазобоя ===")
        print("Откроется окно для настройки Вазобоя...")
        vasebreaker_settings = get_vasebreaker_settings()
        if not vasebreaker_settings:
            print("Создание уровня отменено")
            return
    
    print("\n=== Основная информация об уровне ===")
    name = get_alphanumeric_input("Введите название уровня: ")
    description = get_alphanumeric_input("Введите описание уровня: ")
    level_number = get_valid_integer("Введите номер уровня: ")
    
    starting_sun = 0
    if level_type != "vasebreaker" and not (last_stand_settings and last_stand_settings["enable"]):
        starting_sun = get_valid_integer("Введите начальное количество солнца: ")
    
    stage_options = [(i, stage) for i, stage in enumerate(editor.available_stages, 1)]
    stage = select_from_list(stage_options, "Выбор лужайки")
    
    conveyor_settings = None
    if level_type == "conveyor":
        conveyor_settings = get_conveyor_settings(editor)
    
    print("\n=== Настройка челленджей ===")
    challenges = {}
    if get_yes_no_input("Добавить челленджи?"):
        challenges = get_challenge_settings()
    
    print("\n=== Дополнительные свойства уровня ===")
    level_properties = {}
    if get_yes_no_input("Настроить дополнительные свойства уровня?"):
        level_properties = get_level_properties(editor)
    
    editor.create_new_level(
        name=name,
        description=description,
        level_number=level_number,
        stage=stage,
        level_type=level_type,
        last_stand_settings=last_stand_settings,
        conveyor_settings=conveyor_settings,
        challenges=challenges,
        level_properties=level_properties,
        zomboss_settings=zomboss_settings,
        vasebreaker_settings=vasebreaker_settings
    )
    
    if level_type != "vasebreaker":
        print("\n=== Настройка волн ===")
        wave_count = get_valid_integer("Сколько волн должен иметь уровень?: ")
        
        if wave_count > 0:
            editor.set_wave_properties(
                flag_wave_interval=get_valid_integer("Интервал между флаг-волнами (минимум 1): ", 1),
                wave_count=wave_count,
                first_wave_delay=get_valid_integer("Задержка перед первой волной: ")
            )
            
            for wave_num in range(wave_count):
                zombies, counts, plantfood = get_zombie_wave_settings(wave_num, editor)
                editor.add_wave(zombies, counts, plantfood)
        else:
            print("Уровень будет без волн (авто-победа)")
            editor.set_wave_properties(
                flag_wave_interval=1,
                wave_count=0,
                first_wave_delay=1
            )
    else:
        editor.set_wave_properties(
            flag_wave_interval=1,
            wave_count=0,
            first_wave_delay=1
        )
    
    print("\n=== Награды за уровень ===")
    if get_yes_no_input("Добавить награду за уровень?"):
        if reward_plant := get_plant_reward():
            editor.set_rewards("unlock_plant", reward_plant)
    else:
        editor.set_rewards(None, None)
    
    filename = f"{name.lower().replace(' ', '_')}.json"
    editor.save_level(filename)
    print(f"\nУровень успешно создан! Сохранён в файл {filename}")

if __name__ == "__main__":
    main()
