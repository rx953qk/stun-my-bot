import sys
import subprocess
import time
from pathlib import Path


def ensure_packages():
    """Auto-install minimal dependencies used by the framework."""
    required = ["pyzmq", "loguru", "json5", "pywin32"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])


ensure_packages()

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from jduel_bot.jduel_bot_client import JDuelBotClient, master_duel_connection_address, Coordinates
from jduel_bot.jduel_bot_enums import (
    Phase,
    CommandType,
    CommandBit,
    Player,
    CardPosition,
    CardSelection,
    DialogButtonType,
    CardFace,
    CardTurn,
)
from jduel_bot.jduel_bot_handler import JDuelBotHandler
from jduel_bot.jduel_bot_logger import LoggerManager, get_log_filename


COMMAND_BIT_TO_TYPE = {
    CommandBit.Attack: CommandType.Attack,
    CommandBit.Look: CommandType.Look,
    CommandBit.SummonSp: CommandType.SummonSp,
    CommandBit.Action: CommandType.Action,
    CommandBit.Summon: CommandType.Summon,
    CommandBit.Reverse: CommandType.Reverse,
    CommandBit.SetMonst: CommandType.SetMonst,
    CommandBit.Set: CommandType.Set,
    CommandBit.Pendulum: CommandType.Pendulum,
    CommandBit.TurnAtk: CommandType.TurnAtk,
    CommandBit.TurnDef: CommandType.TurnDef,
    CommandBit.Surrender: CommandType.Surrender,
    CommandBit.Decide: CommandType.Decide,
    CommandBit.Draw: CommandType.Draw,
}

TimeTearingMorganite = {"Time-Tearing Morganite", 250, "spell", "continuous_spell"}

PotOfDuality = {"Pot of Duality", 240, "spell", "draw_spell"}
PotOfExtravagance = {"Pot of Extravagance", 230, "spell", "draw_spell"}
PotOfDesires = {"Pot of Desires", 220, "spell", "draw_spell"}

InspectorBoarder = {"Inspector Boarder", 200, "monster", "monster_stun"}
FossilDyna = {"Fossil Dyna Pachycephalo", 195, "monster", "monster_stun"}
ThunderKingRaiOh = {"Thunder King Rai-Oh", 190, "monster", "monster_stun"}
BarrierStatueInferno = {"Barrier Statue of the Inferno", 185, "monster", "monster_stun"}
BarrierStatueTorrent = {"Barrier Statue of the Torrent", 180, "monster", "monster_stun"}
BanisherRadiance = {"Banisher of the Radiance", 175, "monster", "monster_stun"}

Necrovalley = {"Necrovalley", 150, "spell", "field_spell"}
ClockworkNight = {"Clockwork Night", 145, "spell", "continuous_spell"}

SuperPolymerization = {"Super Polymerization", 120, "spell", "board_breaker"}

DimensionShifter = {"Dimension Shifter", 115, "monster", "hand_trap"}
ArtifactLancea = {"Artifact Lancea", 110, "monster", "hand_trap"}

MacroCosmos = {"Macro Cosmos", 160, "trap", "continuous_trap"}
ThereCanBeOnlyOne = {"There Can Be Only One", 155, "trap", "continuous_trap"}

SolemnJudgment = {"Solemn Judgment", 105, "trap", "negate_trap"}
SolemnStrike = {"Solemn Strike", 104, "trap", "negate_trap"}
SolemnWarning = {"Solemn Warning", 103, "trap", "negate_trap"}
IronThunder = {"Iron Thunder", 102, "trap", "negate_trap"}

DominusImpulse = {"Dominus Impulse", 101, "trap", "negate_trap"}
DominusPurge = {"Dominus Purge", 100, "trap", "negate_trap"}

InfiniteImpermanence = {"Infinite Impermanence", 99, "trap", "negate_trap"}

UnendingNightmare = {"Unending Nightmare", 95, "trap", "utility_trap"}

# Priority for choosing actions (higher = prefer earlier). Used by _choose_best_action.
HAND_PRIORITY = {
    "Time-Tearing Morganite": 250,
    "Pot of Duality": 240,
    "Pot of Extravagance": 230,
    "Pot of Desires": 220,
    "Inspector Boarder": 200,
    "Fossil Dyna Pachycephalo": 195,
    "Thunder King Rai-Oh": 190,
    "Barrier Statue of the Inferno": 185,
    "Barrier Statue of the Torrent": 180,
    "Banisher of the Radiance": 175,
    "Necrovalley": 150,
    "Clockwork Night": 160,  # Prefer over TCBOO when both in hand
    "Super Polymerization": 120,
    "Dimension Shifter": 115,
    "Artifact Lancea": 110,
    "Macro Cosmos": 160,
    "There Can Be Only One": 155,  # Lower than Clockwork Night (160) when both in hand
    "Solemn Judgment": 105,
    "Solemn Strike": 104,
    "Solemn Warning": 103,
    "Iron Thunder": 102,
    "Dominus Impulse": 101,
    "Dominus Purge": 100,
    "Infinite Impermanence": 99,
    "Unending Nightmare": 95,
}
# Monsters we do not normal summon (hand-trap style).
NEVER_SUMMON = {"Dimension Shifter", "Artifact Lancea"}
# Prefer summoning these on turn 1 (when going first); when going second prefer highest ATK.
MONSTER_STUN_NAMES = {
    "Inspector Boarder", "Fossil Dyna Pachycephalo", "Thunder King Rai-Oh",
    "Barrier Statue of the Inferno", "Barrier Statue of the Torrent", "Banisher of the Radiance",
}
NEVER_SET_FROM_HAND = {"Artifact Lancea"}

# Artifact Lancea: only activate from hand vs banish-heavy decks.
LANCEA_NAME = "Artifact Lancea"
LANCEA_ANTI_BANISH_DECK_KEYWORDS = {
    # Kashtira
    "Kashtira", "Fenrir", "Unicorn", "Theosis", "Birth", "Riseheart", "Arise-Heart",
    # Runick
    "Runick", "Hugin", "Fountain", "Tip", "Munin",
    # Floowandereeze
    "Floowandereeze", "Robina", "Eaglen", "Empen", "Map", "Advent",
    # Dragon Link (heuristic)
    "Rokket", "Borrel", "Striker Dragon", "Chaos Space", "Dragon Ravine", "Boot Sector",
    # Branded (partial)
    "Branded", "Aluber", "Fallen of Albaz", "Mirrorjade", "Lubellion", "Bystial",
}

# Setting: do not set duplicate names on field, except these may be set in multiple copies.
SET_ALLOW_DUPLICATE_NAMES = {"Infinite Impermanence"}

# Negate traps: used to respond to opponent's actions -> must be used first (priority when chaining).
NEGATE_TRAP_NAMES = {
    "Solemn Judgment", "Solemn Strike", "Solemn Warning",
    "Iron Thunder", "Dominus Impulse", "Dominus Purge", "Infinite Impermanence",
}
# Continuous traps: activate when possible but always after negate traps when chaining.
CONTINUOUS_TRAP_NAMES = {"Macro Cosmos", "There Can Be Only One", "Unending Nightmare"}
# Solemn can negate any opponent effect -> always priority when chaining.
SOLEMN_NAMES = {"Solemn Judgment", "Solemn Strike", "Solemn Warning"}
# CardPosition Monster = 0 .. MonsterEnd = 6 (monster zones)
MONSTER_ZONE_POSITION_MAX = 6
INFINITE_IMPERMANENCE_NAME = "Infinite Impermanence"
DOMINUS_IMPULSE_NAME = "Dominus Impulse"
CLOCKWORK_NIGHT_NAME = "Clockwork Night"
TCBOO_NAME = "There Can Be Only One"

# Draw spells: use first when playing proactively (not chaining).
DRAW_SPELL_NAMES = {"Pot of Duality", "Pot of Extravagance", "Pot of Desires"}
# Only Pot of Duality/Pot of Extravagance need special dialog handling.
POT_OF_DUALITY_NAME = "Pot of Duality"
POT_OF_EXTRAVAGANCE_NAME = "Pot of Extravagance"
UNENDING_NIGHTMARE_NAME = "Unending Nightmare"
SUPER_POLY_NAME = "Super Polymerization"




class LockdownStunBotHandler(JDuelBotHandler):
    def __init__(self, duel_bot_client: JDuelBotClient, logger):
        super().__init__(duel_bot_client, logger)
self.first_card_activation_coordinates = {"YES": Coordinates(741, 425), "NO": Coordinates(541, 425)}
        # Super Polymerization: multi-stage prompt tracking (avoid mis-detect / infinite loop)
        self._super_poly_cost_pending_until = 0.0
        # stages: none | discard | materials | fusion | position | zone (summon zone selection)
        self._super_poly_stage = "none"
        # Position prompt (Face-Up ATK/DEF) coordinates (1280x720)
        self._pos_faceup_atk = Coordinates(568, 580)
        self._pos_faceup_def = Coordinates(712, 580)
        # Unending Nightmare: only handle YES/NO prompt after we actually activate it (Action)
        self._unending_prompt_pending_until = 0.0
        


    # ===== Get all valid actions from the game =====
    def _get_all_valid_actions(self):
        valid_actions = []
        board_state = self.duel_bot_client.get_board_state()
        my_state = board_state.player_card_states[Player.Myself]

        # Hand: Summon, Set, Action (activate from hand)
        for i, card in enumerate(my_state.hand):
            if not card:
                continue
            atk_val = getattr(card, "attack", None)
            if atk_val is None:
                atk_val = getattr(card, "atk", 0)
            for bit in card.command_bits:
                if bit in COMMAND_BIT_TO_TYPE:
                    valid_actions.append({
                        "player": Player.Myself,
                        "position": CardPosition.Hand,
                        "index": i,
                        "command_type": COMMAND_BIT_TO_TYPE[bit],
                        "card_name": card.name,
                        "action_name": bit.name,
                        "type": getattr(card, "type", "") or "",
                        "typeline": getattr(card, "typeline", "") or "",
                        "attack": atk_val,
                    })

        # Field: monsters and spells_and_traps (activate on field)
        for zone, base_pos in (
            (my_state.monsters, CardPosition.Monster),
            (my_state.spells_and_traps, CardPosition.Magic),
        ):
            for i, card in enumerate(zone):
                if not card:
                    continue
                for bit in card.command_bits:
                    if bit in COMMAND_BIT_TO_TYPE:
                        valid_actions.append({
                            "player": Player.Myself,
                            "position": CardPosition(base_pos + i),
                            "index": i,
                            "command_type": COMMAND_BIT_TO_TYPE[bit],
                            "card_name": card.name,
                            "action_name": bit.name,
                            "type": getattr(card, "type", "") or "",
                            "typeline": getattr(card, "typeline", "") or "",
                        })

        return valid_actions

    def _filter_set_duplicates(self, valid_actions):
        """Remove Set actions that would duplicate a card name on field, except Infinite Impermanence."""
        board_state = self.duel_bot_client.get_board_state()
        my_state = board_state.player_card_states[Player.Myself]
        names_on_field = {c.name for c in my_state.spells_and_traps if c}
        out = []
        for a in valid_actions:
            if a["command_type"] == CommandType.Set and a["position"] == CardPosition.Hand:
                if a["card_name"] in NEVER_SET_FROM_HAND:
                    continue
                # Normal/Quick-Play spells must not be set, except Super Polymerization.
                card_type = str(a.get("type", "") or "")
                card_typeline = str(a.get("typeline", "") or "")
                is_spell = "Spell" in card_type or "Spell" in card_typeline
                is_field = "Field" in card_type or "Field" in card_typeline
                is_continuous = "Continuous" in card_type or "Continuous" in card_typeline
                if (
                    is_spell
                    and not is_field
                    and not is_continuous
                    and a["card_name"] != SUPER_POLY_NAME
                ):
                # e.g. Pot of Duality/Desires/Extravagance, Time-Tearing Morganite must be activated from hand, not set.
                    continue
                # If one of Clockwork Night / There Can Be Only One is already on field (set or face-up),
                # do not Set the other (avoid conflict). Only block when the OTHER card is on field.
                if a["card_name"] in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME}:
                    conflict_present = False
                    for st in my_state.spells_and_traps or []:
                        if not st:
                            continue
                        if st.name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME} and st.name != a["card_name"]:
                            conflict_present = True
                            break
                    if conflict_present:
                        continue
                if a["card_name"] in names_on_field and a["card_name"] not in SET_ALLOW_DUPLICATE_NAMES:
                    continue
            out.append(a)
        return out

    def _opponent_is_anti_lancea_target(self) -> bool:
        """Heuristic: detect if opponent's deck is a good Lancea target."""
        try:
            board = self.duel_bot_client.get_board_state()
            opp = board.player_card_states.get(Player.Opponent)
            if not opp:
                return False

            seen: list[str] = []
            # Hand may not be readable; if readable, use it.
            for c in (opp.hand or []):
                if c and getattr(c, "name", None):
                    seen.append(str(c.name))
            for zone in (opp.monsters, opp.spells_and_traps, opp.graveyard, opp.banished):
                for c in (zone or []):
                    if c and getattr(c, "name", None):
                        seen.append(str(c.name))
            if opp.field_spell and getattr(opp.field_spell, "name", None):
                seen.append(str(opp.field_spell.name))

            for name in seen:
                for kw in LANCEA_ANTI_BANISH_DECK_KEYWORDS:
                    if kw in name:
                        return True
        except Exception:
            pass
        return False

    def _try_activate_lancea_if_available(self) -> bool:
        """On opponent's turn with chain prompt: if Lancea in hand is activatable (Action) and matchup fits, activate it."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if self.duel_bot_client.is_my_turn():
                return False
            if not self._opponent_is_anti_lancea_target():
                return False

            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            if not my_state:
                return False

            for idx, c in enumerate(my_state.hand or []):
                if not c or str(getattr(c, "name", "")) != LANCEA_NAME:
                    continue
                if CommandBit.Action not in (getattr(c, "command_bits", []) or []):
                    self.logger.info("[Lancea] On hand but not activatable now (no Action).")
                    return False

                self.logger.info("[Lancea] Activatable on opponent prompt -> activating from hand")
                self.duel_bot_client.activate_monster_effect_from_hand(idx)
                self.duel_bot_client.wait_for_input_enabled()
                return True
        except Exception as e:
            self.logger.warning(f"[Lancea] Activation failed: {e}")
        return False

    def _pick_discard_index_for_cost(self) -> int | None:
        """Pick hand index to discard (cost). Prefer discarding the lowest-priority card."""
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            if not my_state:
                return None

            best_idx = None
            best_score = None  # lower is better (we discard the least valuable)
            for i, c in enumerate(my_state.hand or []):
                if not c or not getattr(c, "name", None):
                    continue
                name = str(c.name)
                if name == SUPER_POLY_NAME:
                    continue
                score = HAND_PRIORITY.get(name, 10)
                if best_score is None or score < best_score:
                    best_score = score
                    best_idx = i

            return best_idx
        except Exception:
            return None

    def _handle_super_poly_discard_prompt(self) -> bool:
        """Super Polymerization: on activation requires discarding 1 from hand -> auto pick one and confirm."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if getattr(self, "_super_poly_stage", "none") != "discard":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                last_used = ""
            if last_used != SUPER_POLY_NAME:
                return False

            idx = self._pick_discard_index_for_cost()
            if idx is None:
                self.logger.warning("[Super Poly] No discard candidate found; cancelling prompt.")
                self.duel_bot_client.cancel_activation_prompts()
                self._super_poly_cost_pending_until = 0.0
                self._super_poly_stage = "none"
                return True

            # Try a few indices/buttons (some prompts map to different confirm buttons)
            candidates = [idx, 0, 1, 2, 3, 4, 5]
            seen = set()
            for cand in candidates:
                if cand in seen:
                    continue
                seen.add(cand)
                self.logger.info(f"[Super Poly] Discard cost: try hand index={cand} (Middle)")
                try:
                    self.duel_bot_client.select_cards_from_dialog(
                        [CardSelection(card_index=cand)],
                        dialog_button_type=DialogButtonType.Middle,  # Select / OK
                        milliseconds_delay_between_clicks=200,
                    )
                    self.duel_bot_client.wait_for_input_enabled()
                    if not self.duel_bot_client.is_inputting():
                        self._super_poly_cost_pending_until = 0.0
                        self._super_poly_stage = "none"
                        return True
                except Exception:
                    pass

                self.logger.info(f"[Super Poly] Discard cost: try hand index={cand} (Right)")
                try:
                    self.duel_bot_client.select_cards_from_dialog(
                        [CardSelection(card_index=cand)],
                        dialog_button_type=DialogButtonType.Right,
                        milliseconds_delay_between_clicks=200,
                    )
                    self.duel_bot_client.wait_for_input_enabled()
                    if not self.duel_bot_client.is_inputting():
                        self._super_poly_cost_pending_until = 0.0
                        self._super_poly_stage = "none"
                        return True
                except Exception:
                    pass

            # If still inputting, likely moved to Fusion Material selection -> switch stage
            self.logger.info("[Super Poly] After discard attempt still inputting -> switching to materials stage.")
            self._super_poly_stage = "materials"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Discard prompt handle failed: {e}")
            return False

    def _handle_super_poly_material_prompt(self) -> bool:
        """Super Polymerization: after discard, requires selecting 2 monsters as Fusion Material."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if getattr(self, "_super_poly_stage", "none") != "materials":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                self._super_poly_stage = "none"
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                last_used = ""
            if last_used != SUPER_POLY_NAME:
                return False

            board = self.duel_bot_client.get_board_state()
            opp = board.player_card_states.get(Player.Opponent)
            my = board.player_card_states.get(Player.Myself)

            def collect(state, faceup_only: bool):
                out = []
                if not state:
                    return out
                for m in state.monsters or []:
                    if not m or getattr(m, "position", None) is None:
                        continue
                    if faceup_only and getattr(m, "face", None) != CardFace.FaceUp:
                        continue
                    out.append(m.position)
                return out

            candidates = []
            candidates += collect(opp, True)
            candidates += collect(opp, False)
            if len(set(candidates)) < 2:
                candidates += collect(my, False)

            uniq = []
            seen = set()
            for p in candidates:
                if p in seen:
                    continue
                seen.add(p)
                uniq.append(p)

            if len(uniq) < 2:
                self.logger.warning("[Super Poly] Not enough monsters to select materials; cancelling.")
                self.duel_bot_client.cancel_activation_prompts()
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            p1, p2 = uniq[0], uniq[1]
            self.logger.info(f"[Super Poly] Selecting fusion materials: {p1.name}, {p2.name}")

            # Select two monsters by targeting them (field selection)
            try:
                self.duel_bot_client.target_card(Player.Opponent, p1)
            except Exception:
                self.duel_bot_client.target_card(Player.Myself, p1)
            time.sleep(0.2)
            try:
                self.duel_bot_client.target_card(Player.Opponent, p2)
            except Exception:
                self.duel_bot_client.target_card(Player.Myself, p2)
            time.sleep(0.2)

            # Confirm selection if possible
            try:
                self.duel_bot_client.execute_command(Player.Myself, CardPosition.Select, 0, CommandType.Decide)
                self.duel_bot_client.wait_for_input_enabled()
            except Exception:
                pass

            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            # After selecting materials, game asks for Fusion Monster to summon, then Face-Up ATK/DEF. Switch to fusion stage first.
            self.logger.info("[Super Poly] After selecting materials still inputting -> likely fusion-choice prompt.")
            self._super_poly_stage = "fusion"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Material prompt handle failed: {e}")
            return False

    def _handle_faceup_position_prompt(self) -> bool:
        """Choose Face-Up position (ATK preferred) when game asks after Fusion/Summon."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            # Only handle when in Super Poly flow to avoid clicking wrong prompt
            if getattr(self, "_super_poly_stage", "none") != "position":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                self._super_poly_stage = "none"
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                last_used = ""
            if last_used != SUPER_POLY_NAME:
                return False

            self.logger.info("[Super Poly] Position prompt -> choosing Face-Up Attack")
            self.duel_bot_client.simulate_click(self._pos_faceup_atk)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "zone"
                self._super_poly_cost_pending_until = time.time() + 8.0
                return True

            # fallback: try defense if attack didn't work
            self.logger.info("[Super Poly] Position prompt still inputting -> trying Face-Up Defense")
            self.duel_bot_client.simulate_click(self._pos_faceup_def)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "zone"
                self._super_poly_cost_pending_until = time.time() + 8.0
                return True

            self.logger.warning("[Super Poly] Position prompt still inputting -> cancelling to avoid loop.")
            self.duel_bot_client.cancel_activation_prompts()
            self._super_poly_stage = "none"
            self._super_poly_cost_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Position prompt handle failed: {e}")
            return False

    def _handle_summon_zone_prompt(self) -> bool:
        """After choosing position (ATK/DEF), game asks for summon zone — click one empty monster zone."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if getattr(self, "_super_poly_stage", "none") != "zone":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return False
            board = self.duel_bot_client.get_board_state()
            pos = self.duel_bot_client.get_free_monster_card_zone(board)
            if not pos:
                self.logger.warning("[Super Poly] Summon zone prompt: no free monster zone.")
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True
            self.logger.info(f"[Super Poly] Summon zone prompt -> selecting summon zone: {pos.name}")
            self.duel_bot_client.click_my_monster_zone(pos)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            self._super_poly_stage = "none"
            self._super_poly_cost_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Summon zone prompt handle failed: {e}")
            return False

    def _handle_super_poly_fusion_prompt(self) -> bool:
        """After selecting materials, Super Poly opens dialog to choose Fusion Monster to summon."""
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if getattr(self, "_super_poly_stage", "none") != "fusion":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                self._super_poly_stage = "none"
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                last_used = ""
            if last_used != SUPER_POLY_NAME:
                return False

            # Brief wait for dialog to fully appear
            time.sleep(0.3)
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            # Dialog is usually Fusion Monster list – often only one choice. Select index 0.
            self.logger.info("[Super Poly] Fusion prompt -> selecting first fusion monster (index=0)")
            try:
                self.duel_bot_client.select_card_from_dialog(
                    CardSelection(card_index=0),
                    dialog_button_type=DialogButtonType.Middle,
                    milliseconds_delay_between_clicks=200,
                )
                self.duel_bot_client.wait_for_input_enabled()
            except Exception as e:
                self.logger.warning(f"[Super Poly] Fusion select via dialog failed: {e}")

            if not self.duel_bot_client.is_inputting():
                # Game may have auto-selected position; reset stage.
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            # Still prompting -> likely moved to position selection.
            self.logger.info("[Super Poly] After fusion choice still inputting -> likely position prompt.")
            self._super_poly_stage = "position"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Fusion prompt handle failed: {e}")
            return False

    def _try_flip_my_facedown_monsters(self) -> None:
        """Before Battle: if our monsters are face-down, try to flip them if game allows (CommandBit.Reverse)."""
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            for m in (my_state.monsters if my_state else []) or []:
                if not m:
                    continue
                if getattr(m, "face", None) != CardFace.FaceDown:
                    continue
                pos = getattr(m, "position", None)
                if pos is None:
                    continue
                bits = getattr(m, "command_bits", []) or []
                if CommandBit.Reverse not in bits:
                    self.logger.info(f"[PreBattleFlip] Skip {m.name} ({pos.name}) — no Reverse available.")
                    continue
                try:
                    self.logger.info(f"[PreBattleFlip] Flip summon {m.name} ({pos.name})")
                    self.duel_bot_client.perform_flip_summon(pos)
                    self.duel_bot_client.handle_unexpected_prompts()
                    time.sleep(0.2)
                except Exception as e:
                    self.logger.warning(f"[PreBattleFlip] Flip summon failed for {m.name}: {e}")
        except Exception as e:
            self.logger.warning(f"[PreBattleFlip] Scan failed: {e}")

    def _infer_last_used_owner_and_type(self, last_used: str):
        """Heuristic: infer from current board whether last_used belongs to which side and is a monster."""
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            opp_state = board.player_card_states.get(Player.Opponent)

            def scan(state, player: Player):
                if not state:
                    return None
                # Monsters
                for c in state.monsters or []:
                    if c and str(c.name) == last_used:
                        return player, True
                # S/T
                for c in state.spells_and_traps or []:
                    if c and str(c.name) == last_used:
                        return player, False
                # Field
                if state.field_spell and str(state.field_spell.name) == last_used:
                    return player, False
                return None

            res = scan(opp_state, Player.Opponent)
            if res:
                return res
            res = scan(my_state, Player.Myself)
            if res:
                return res
        except Exception:
            pass
        return None, False

    def _get_response_context(self):
        """
        Return (top_player, is_monster_effect, source) to decide chain negate.
        Prefer get_chain_data(); if chain_data is wrong/stale, fallback to last_used + board scan.
        """
        top_player = None
        is_monster_effect = False
        source = "none"
        try:
            chain_data = self.duel_bot_client.get_chain_data()
            if chain_data:
                top = chain_data[-1]
                top_player = getattr(top, "player", None)
                top_position = getattr(top, "position", None)
                if top_position is not None:
                    pos_val = int(top_position)
                    is_monster_effect = 0 <= pos_val <= MONSTER_ZONE_POSITION_MAX
                source = "chain"
        except Exception:
            pass

        last_used = ""
        try:
            last_used = self.duel_bot_client.get_last_used_card_name()
        except Exception:
            last_used = ""

        if last_used:
            inferred_player, inferred_is_monster = self._infer_last_used_owner_and_type(last_used)
            # If chain says Myself but last_used is clearly opponent's card on field -> override to not miss II/Solemn chain
            if inferred_player is not None and (top_player is None or top_player == Player.Myself) and inferred_player == Player.Opponent:
                top_player = Player.Opponent
                is_monster_effect = inferred_is_monster
                source = f"last_used:{last_used}"
            # If no chain, use inferred
            if top_player is None and inferred_player is not None:
                top_player = inferred_player
                is_monster_effect = inferred_is_monster
                source = f"last_used:{last_used}"

        return top_player, is_monster_effect, source

    def _choose_best_action(self, valid_actions):
        """Pick one action by priority; only Summon, Action, Set from hand; Action from field.
        Detect opponent chain: avoid negating our own cards; prefer Solemn; II only when opponent activates monster effect."""
        if not valid_actions:
            return None
        board_state = self.duel_bot_client.get_board_state()
        my_state = board_state.player_card_states[Player.Myself]
        opp_state = board_state.player_card_states.get(Player.Opponent)
        top_player, is_monster_effect_chain, ctx_src = self._get_response_context()
        if top_player is not None:
            self.logger.info(f"[Chain] Top player={top_player}, is_monster_effect={is_monster_effect_chain} (src={ctx_src})")
        best = None
        best_score = -1
        for action in valid_actions:
            card_name = action["card_name"]
            cmd = action["command_type"]
            pos = action["position"]
            if pos == CardPosition.Hand and cmd not in (CommandType.Summon, CommandType.Action, CommandType.Set):
                continue
            if cmd == CommandType.Summon and card_name in NEVER_SUMMON:
                continue
            # Allow Action on field and TurnAtk (switch Defense -> Attack before attacking).
            if pos != CardPosition.Hand and cmd not in (CommandType.Action, CommandType.TurnAtk):
                continue
            # Default by HAND_PRIORITY; for hand Summon: turn 1 (going first) prefer monster_stun, going second prefer highest ATK.
            if pos == CardPosition.Hand and cmd == CommandType.Summon:
                atk_val = int(action.get("attack", 0) or 0)
                try:
                    turn_num = self.duel_bot_client.get_turn_number()
                except Exception:
                    turn_num = 2
                if turn_num == 1:
                    # Turn 1 (going first): prefer monster_stun by HAND_PRIORITY.
                    if card_name in MONSTER_STUN_NAMES:
                        base_priority = 400 + HAND_PRIORITY.get(card_name, 0)
                    else:
                        base_priority = 300 + atk_val
                else:
                    # Going second or later: prefer highest ATK.
                    base_priority = 300 + atk_val
            elif cmd == CommandType.TurnAtk:
                # Prefer switching Defense -> Attack so we can attack in Battle Phase.
                base_priority = 250
            else:
                base_priority = HAND_PRIORITY.get(card_name, 10)
            # Extra Deck Mudragon: do not activate effect, use as body only
            if cmd == CommandType.Action and card_name == "Mudragon of the Swamp":
                self.logger.info("[Mudragon] Skip Action — effect not needed, skip prompt.")
                continue
            # Super Polymerization: to avoid hitting our cards, only activate when opponent has >= 2 monsters on field
            if cmd == CommandType.Action and card_name == SUPER_POLY_NAME:
                opp_monster_count = 0
                if opp_state:
                    for m in (opp_state.monsters or []):
                        if m and getattr(m, "position", None) is not None:
                            opp_monster_count += 1
                if opp_monster_count < 2:
                    self.logger.info(f"[Super Poly] Skip activation — opponent monsters={opp_monster_count} (<2).")
                    continue
            # Artifact Lancea: do not set; only chain activate from hand when opponent is banish-deck type
            if pos == CardPosition.Hand and card_name == LANCEA_NAME:
                if cmd == CommandType.Set:
                    continue
                if cmd == CommandType.Action:
                    if top_player != Player.Opponent:
                        continue
                    if not self._opponent_is_anti_lancea_target():
                        self.logger.info("[Lancea] Skip — opponent not banish-deck type (heuristic).")
                        continue
                    base_priority = 700  # after Solemn, before normal negate
            # Dimension Shifter: if in hand and game offers Action, always prefer activating early.
            if pos == CardPosition.Hand and card_name == "Dimension Shifter" and cmd == CommandType.Action:
                base_priority = 750  # higher than Lancea, lower than Solemn
            # --- Clockwork Night / There Can Be Only One: if one is already on field (face-down or face-up),
            #     the other must not be Set/Activated. Only block when the OTHER card is on field ---
            if card_name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME}:
                conflict_on_field = False
                for st in my_state.spells_and_traps or []:
                    if not st:
                        continue
                    if st.name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME} and st.name != card_name:
                        # Other card already on field (set or face-up) -> that rule is chosen, skip this one.
                        conflict_on_field = True
                        break
                if conflict_on_field:
                    self.logger.info(f"[Clockwork/TCBOO] Skip '{card_name}' — other conflicting card already on field.")
                    continue
            # --- Avoid activating duplicate Continuous Spell already on field (e.g. Clockwork Night) ---
            if pos == CardPosition.Hand and cmd == CommandType.Action and card_name in {CLOCKWORK_NIGHT_NAME, "Time-Tearing Morganite"}:
                if any(c and c.name == card_name for c in my_state.spells_and_traps):
                    self.logger.info(f"[Spell] Skip '{card_name}' — already on field, do not activate second copy.")
                    continue
            # --- Draw spells: use first when playing proactively (no chain) ---
            if top_player is None and cmd == CommandType.Action and card_name in DRAW_SPELL_NAMES:
                base_priority += 100
            # --- Unending Nightmare: activate when opponent has any face-up S/T ---
            if cmd == CommandType.Action and card_name == UNENDING_NIGHTMARE_NAME:
                if not self._has_opponent_faceup_spell_trap():
                    self.logger.info(f"[Unending Nightmare] Skip activation — no face-up S/T to destroy.")
                    continue
            # --- Chain logic: negate only when opponent is chain top; avoid negating our own cards ---
            if cmd == CommandType.Action and card_name in NEGATE_TRAP_NAMES:
                if top_player == Player.Myself:
                    self.logger.info(f"[Negate] Skip '{card_name}' — chaining our own card, do not negate.")
                    continue
                if top_player is None:
                    self.logger.info(f"[Negate] Skip '{card_name}' — no opponent chain, no need to negate.")
                    continue
                if top_player == Player.Opponent:
                    if card_name in SOLEMN_NAMES:
                        base_priority = 1000
                    elif card_name == INFINITE_IMPERMANENCE_NAME:
                        # Infinite Impermanence only used to negate opponent's MONSTER effects
                        if not is_monster_effect_chain:
                            self.logger.info(f"[Negate] Skip '{card_name}' — opponent did not activate monster effect.")
                            continue
                        # And only when opponent has at least 1 monster on field to target
                        has_target = False
                        if opp_state:
                            for m in (opp_state.monsters or []):
                                if m and getattr(m, "position", None) is not None:
                                    has_target = True
                                    break
                        if not has_target:
                            self.logger.info(f"[Negate] Skip '{card_name}' — no monster on field to target, avoid stuck dialog.")
                            continue
                        base_priority = 500
                    elif card_name == DOMINUS_IMPULSE_NAME:
                        # Dominus Impulse: stops Special Summon and monster effects.
                        # Many Special Summon cards are Spell/Trap (e.g. Beetrooper Formation),
                        # so cannot rely only on is_monster_effect_chain. Allow chaining to any opponent action.
                        base_priority = 600  # after Solemn, before normal negate
                    else:
                        base_priority = max(base_priority, 400)
            # --- Continuous traps: always after negate; when chaining opponent, low priority ---
            if cmd == CommandType.Action and card_name in CONTINUOUS_TRAP_NAMES and top_player == Player.Opponent:
                # Exception: Unending Nightmare on field + opponent has face-up S/T -> chain to destroy when dialog is up.
                if card_name == UNENDING_NIGHTMARE_NAME and self._has_opponent_faceup_spell_trap():
                    base_priority = max(base_priority, 200)
                else:
                    base_priority = min(base_priority, 50)
                    self.logger.info(f"[Continuous] '{card_name}' — use only after negate, priority lowered to 50.")
            if base_priority > best_score:
                best_score = base_priority
                best = action
        return best

    def _provide_infinite_imperm_target(self) -> bool:
        """After activating Infinite Impermanence: pick opponent monster activating effect (chain preferred), else any monster on field."""
        try:
            # Prefer: chain top (opponent + monster zone)
            try:
                chain_data = self.duel_bot_client.get_chain_data()
            except Exception:
                chain_data = []

            if chain_data:
                top = chain_data[-1]
                top_player = getattr(top, "player", None)
                top_pos = getattr(top, "position", None)
                if top_player == Player.Opponent and top_pos is not None:
                    pos_val = int(top_pos)
                    if 0 <= pos_val <= MONSTER_ZONE_POSITION_MAX:
                        self.logger.info(f"[Infinite Impermanence] Target (chain): {top_pos.name}")
                        self.duel_bot_client.target_card(Player.Opponent, top_pos)
                        time.sleep(0.4)
                        return True

            # Fallback: pick any opponent monster (prefer face-up first)
            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False

            any_mon = None
            faceup_mon = None
            for m in opp_state.monsters or []:
                if not m or getattr(m, "position", None) is None:
                    continue
                any_mon = any_mon or m
                if getattr(m, "face", None) == CardFace.FaceUp:
                    faceup_mon = faceup_mon or m

            target = faceup_mon or any_mon
            if not target:
                return False
            self.logger.info(f"[Infinite Impermanence] Target (fallback): {target.name} ({target.position.name})")
            self.duel_bot_client.target_card(Player.Opponent, target.position)
            time.sleep(0.4)
            return True
        except Exception as e:
            self.logger.warning(f"[Infinite Impermanence] Target failed: {e}")
            return False

    def _execute_action(self, action):
        """Execute one action: Summon, Set, or Activate (from hand or field). Returns True on success."""
        card_name = action["card_name"]
        cmd = action["command_type"]
        idx = action["index"]
        pos = action["position"]
        self.logger.info(f">> Playing: {action['action_name']} on '{card_name}' (index={idx}, pos={pos})")
        try:
            if pos == CardPosition.Hand:
                if cmd == CommandType.Summon:
                    board = self.duel_bot_client.get_board_state()
                    free_pos = self.duel_bot_client.get_free_monster_card_zone(board)
                    if not free_pos:
                        self.logger.warning("No free monster zone to summon.")
                        return False
                    self.duel_bot_client.normal_summon_monster(idx, free_pos)
                    self.duel_bot_client.wait_for_input_enabled()
                elif cmd == CommandType.Set:
                    board = self.duel_bot_client.get_board_state()
                    card_type = action.get("type", "") or ""
                    card_typeline = action.get("typeline", "") or ""
                    is_field = "Field" in card_type or "Field" in card_typeline or card_name == "Necrovalley"
                    st_zone = CardPosition.Field if is_field else self.duel_bot_client.get_free_spell_or_trap_card_zone(board)
                    if not st_zone:
                        self.logger.warning("No free S/T zone to set card.")
                        return False
                    self.logger.info(f"Setting '{card_name}' face-down to {st_zone.name}")
                    self.duel_bot_client.execute_command(Player.Myself, CardPosition.Hand, idx, CommandType.Set)
                    self.duel_bot_client.wait_for_input_enabled()
                    self.duel_bot_client.execute_command(Player.Myself, st_zone, 0, CommandType.Decide)
                    self.duel_bot_client.wait_for_input_enabled()
                elif cmd == CommandType.Action:
                    # Hand-trap monster effects (Lancea/Shifter...) must use activate_monster_effect_from_hand
                    card_type = action.get("type", "") or ""
                    card_typeline = action.get("typeline", "") or ""
                    is_monster = "Monster" in card_type or "Monster" in card_typeline
                    if is_monster:
                        self.logger.info(f"Activating monster effect from hand: '{card_name}'")
                        self.duel_bot_client.activate_monster_effect_from_hand(idx)
                        self.duel_bot_client.wait_for_input_enabled()
                        return True
                    # Infinite Impermanence can activate from hand (when conditions met) to chain negate monster
                    if card_name == INFINITE_IMPERMANENCE_NAME:
                        self.duel_bot_client.execute_command(Player.Myself, CardPosition.Hand, idx, CommandType.Action)
                        self.duel_bot_client.wait_for_input_enabled()
                        if self.duel_bot_client.is_inputting():
                            self._provide_infinite_imperm_target()
                            self.duel_bot_client.wait_for_input_enabled()
                        return True
                    board = self.duel_bot_client.get_board_state()
                    is_field = "Field" in card_type or "Field" in card_typeline or card_name == "Necrovalley"
                    target_zone = CardPosition.Field if is_field else self.duel_bot_client.get_free_spell_or_trap_card_zone(board)
                    if not target_zone:
                        self.logger.warning(f"No free S/T zone to activate {card_name}")
                        return False
                    self.logger.info(f"Activating '{card_name}' to {target_zone.name}")
                    self.duel_bot_client.activate_spell_or_trap_from_hand(idx, target_zone)
                    if card_name == SUPER_POLY_NAME:
                        # Super Poly will open discard cost prompt right after activation
                        self._super_poly_cost_pending_until = time.time() + 12.0
                        self._super_poly_stage = "discard"
                    self.duel_bot_client.wait_for_input_enabled()
                else:
                    return False
            else:
                if cmd == CommandType.Action:
                    self.duel_bot_client.activate_spell_or_trap_from_field(pos)
                    if card_name == UNENDING_NIGHTMARE_NAME:
                        # After activation, game may show YES/NO prompt. Mark a short window to handle it.
                        self._unending_prompt_pending_until = time.time() + 8.0
                    if card_name == SUPER_POLY_NAME:
                        self._super_poly_cost_pending_until = time.time() + 12.0
                        self._super_poly_stage = "discard"
                    self.duel_bot_client.wait_for_input_enabled()
                    if card_name == INFINITE_IMPERMANENCE_NAME and self.duel_bot_client.is_inputting():
                        self._provide_infinite_imperm_target()
                        self.duel_bot_client.wait_for_input_enabled()
                elif cmd == CommandType.TurnAtk:
                    self.logger.info(f"Switch position Defense -> Attack: '{card_name}' ({pos.name})")
                    self.duel_bot_client.turn_attack(pos)
                    self.duel_bot_client.wait_for_input_enabled()
                else:
                    return False
            return True
        except Exception as e:
            self.logger.warning(f"Execute action failed: {e}")
            return False

    def _log_board_state_detail(self):
        """Log hand and field for both sides in detail (for debug)."""
        try:
            board = self.duel_bot_client.get_board_state()
            for player in (Player.Myself, Player.Opponent):
                label = "Myself" if player == Player.Myself else "Opponent"
                state = board.player_card_states.get(player)
                if not state:
                    self.logger.debug(f"[Board] {label}: no state")
                    continue
                hand_names = [c.name if c else "?" for c in state.hand]
                self.logger.info(f"[Board] {label} Hand ({len(hand_names)}): {hand_names}")
                for i, c in enumerate(state.monsters or []):
                    if c:
                        self.logger.info(f"[Board]   {label} Monster[{i}]: {c.name} face={getattr(c, 'face', '?')} turn={getattr(c, 'turn', '?')}")
                for i, c in enumerate(state.spells_and_traps or []):
                    if c:
                        self.logger.info(f"[Board]   {label} S/T[{i}]: {c.name} face={getattr(c, 'face', '?')}")
                if state.field_spell:
                    self.logger.info(f"[Board]   {label} Field: {state.field_spell.name}")
        except Exception as e:
            self.logger.warning(f"[Board] Log board state failed: {e}")

    def _log_prompt_if_inputting(self):
        """Do not rely on dialog list; only log prompt state (is_inputting/last_used/chain)."""
        try:
            if not self.duel_bot_client.is_inputting():
                return
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                pass
            top_player, is_monster_effect_chain, ctx_src = self._get_response_context()
            self.logger.info(
                f"[Prompt] inputting=True last_used='{last_used}' chain_top={top_player} monster_effect={is_monster_effect_chain} (src={ctx_src}) super_poly_stage={getattr(self, '_super_poly_stage', 'none')}"
            )

            # Log currently activatable (Action) options on board/hand (no dialog list)
            try:
                board = self.duel_bot_client.get_board_state()
                my_state = board.player_card_states.get(Player.Myself)
                if my_state:
                    activatable = []
                    # Hand
                    for i, c in enumerate(my_state.hand or []):
                        if c and CommandBit.Action in (getattr(c, "command_bits", []) or []):
                            activatable.append(f"Hand[{i}]:{c.name}")
                    # Field monsters + S/T
                    for c in (my_state.monsters or []):
                        if c and CommandBit.Action in (getattr(c, "command_bits", []) or []):
                            activatable.append(f"{c.position.name}:{c.name}")
                    for c in (my_state.spells_and_traps or []):
                        if c and CommandBit.Action in (getattr(c, "command_bits", []) or []):
                            activatable.append(f"{c.position.name}:{c.name}")
                    if activatable:
                        self.logger.info(f"[Prompt] Activatable(Action) now: {activatable}")
            except Exception:
                pass
        except Exception as e:
            self.logger.warning(f"[Prompt] Log failed: {e}")

    def _handle_pot_of_duality_dialog(self):
        """After activating Pot of Duality, game opens 3-card dialog — pick one by priority (rest without dialog)."""
        try:
            if not self.duel_bot_client.is_inputting():
                return
            time.sleep(0.4)
            if not self.duel_bot_client.is_inputting():
                return
            cards = self.duel_bot_client.get_dialog_card_list()
            if len(cards) != 3:
                self.logger.warning(f"[Pot of Duality] Dialog does not have 3 cards: {len(cards)} -> {cards}")
                return
            best = max(cards, key=lambda c: HAND_PRIORITY.get(str(c), 0))
            idx = cards.index(best) if best in cards else 0
            self.logger.info(f"[Pot of Duality] Pick 1/3 from dialog -> '{best}' (index={idx})")
            self.duel_bot_client.select_card_from_dialog(
                CardSelection(card_index=idx),
                dialog_button_type=DialogButtonType.Middle,
                milliseconds_delay_between_clicks=200,
            )
            self.duel_bot_client.wait_for_input_enabled()
        except Exception as e:
            self.logger.warning(f"[Pot of Duality] Dialog card selection failed: {e}")
            self.duel_bot_client.cancel_activation_prompts()

    def _handle_pot_of_extravagance_dialog(self):
        """After activating Pot of Extravagance, dialog asks for 3 or 6.
        Prefer 6 (banish more; this deck does not rely on Extra)."""
        try:
            if not self.duel_bot_client.is_inputting():
                return
            # Brief wait for UI to settle
            time.sleep(0.4)
            if not self.duel_bot_client.is_inputting():
                return

            # Dialog 3/6 is a list with 2 option rows, not card list.
            # At 1280x720 we click by coordinates: pick 6 cards (second row), then OK button.
            three_option = Coordinates(610, 270)  # second row "6 card(s)"
            six_option = Coordinates(610, 320)   # second row "6 card(s)"
            ok_button = Coordinates(640, 540)    # OK button

            self.logger.info("[Pot of Extravagance] Click 6 cards option by coordinates.")
            try:
                self.duel_bot_client.simulate_click(six_option)
                time.sleep(0.2)
                self.duel_bot_client.simulate_click(ok_button)
                self.duel_bot_client.wait_for_input_enabled()
            except Exception as e:
                self.logger.warning(f"[Pot of Extravagance] Coordinate click failed: {e}")

            # If still in dialog after click, cancel to avoid lock.
            if self.duel_bot_client.is_inputting():
                self.logger.warning("[Pot of Extravagance] Still inputting after coordinate clicks -> cancel dialog to avoid lock.")
                self.duel_bot_client.cancel_activation_prompts()
        except Exception as e:
            self.logger.warning(f"[Pot of Extravagance] Dialog 3/6 selection failed: {e}")
            self.duel_bot_client.cancel_activation_prompts()

    def _has_opponent_continuous_or_field_faceup(self):
        """Does opponent have any face-up Continuous or Field S/T?"""
        try:
            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False
            for st in opp_state.spells_and_traps or []:
                if not st or st.face != CardFace.FaceUp:
                    continue
                t = str(getattr(st, "type", "") or "")
                tl = str(getattr(st, "typeline", "") or "")
                if "Continuous" in t or "Continuous" in tl or "Field" in t or "Field" in tl:
                    return True
            if opp_state.field_spell and opp_state.field_spell.face == CardFace.FaceUp:
                return True
        except Exception:
            pass
        return False

    def _has_opponent_faceup_spell_trap(self):
        """Does opponent have any face-up S/T? (Unending Nightmare targets 1 face-up S/T.)"""
        try:
            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False
            for st in opp_state.spells_and_traps or []:
                if st and st.face == CardFace.FaceUp:
                    return True
            if opp_state.field_spell and opp_state.field_spell.face == CardFace.FaceUp:
                return True
        except Exception:
            pass
        return False

    def _provide_unending_nightmare_target(self):
        """Pick target: 1 face-up S/T of opponent (Unending Nightmare destroys 1 face-up S/T)."""
        try:
            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False
            for st in opp_state.spells_and_traps or []:
                if not st or st.face != CardFace.FaceUp:
                    continue
                self.logger.info(f"[Unending Nightmare] Target: {st.name} ({st.position.name})")
                self.duel_bot_client.target_card(Player.Opponent, st.position)
                time.sleep(1.0)
                return True
            if opp_state.field_spell and opp_state.field_spell.face == CardFace.FaceUp:
                self.logger.info(f"[Unending Nightmare] Target Field: {opp_state.field_spell.name}")
                self.duel_bot_client.target_card(Player.Opponent, CardPosition.Field)
                time.sleep(1.0)
                return True
        except Exception as e:
            self.logger.warning(f"[Unending Nightmare] Target failed: {e}")
        return False

    def _handle_unending_nightmare_prompt(self) -> bool:
        """
        Do not use dialog list.
        - First Unending Nightmare activation has YES/NO: only YES if opponent has face-up S/T.
        - Later activations ask for target directly -> pick target (no YES/NO).
        Returns True if Unending Nightmare-related prompt was handled.
        """
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            # Only handle if we recently ACTIVATED Unending Nightmare (Action),
            # not when we just Set it (Set can still make last_used == name).
            if time.time() > float(getattr(self, "_unending_prompt_pending_until", 0.0) or 0.0):
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                pass
            if last_used != UNENDING_NIGHTMARE_NAME:
                return False

            has_target = self._has_opponent_faceup_spell_trap()

            # If no target but still prompting, likely first-time YES/NO -> cancel prompt.
            if not has_target:
                self.logger.info("[Unending Nightmare] Cancel (no face-up S/T to destroy)")
                # Try cancelling prompt directly instead of spamming NO (avoid infinite loop).
                try:
                    self.duel_bot_client.cancel_activation_prompts()
                    self.duel_bot_client.wait_for_input_enabled()
                except Exception:
                    pass
                self._unending_prompt_pending_until = 0.0
                return True

            # Has target: first-time flow -> click YES then select target.
            self.logger.info("[Unending Nightmare] YES (has face-up S/T) then select target")
            try:
                # YES button
                self.duel_bot_client.simulate_click(Coordinates(741, 425))
                self.duel_bot_client.wait_for_input_enabled()
                time.sleep(0.3)
            except Exception:
                pass

            if self.duel_bot_client.is_inputting():
                if not self._provide_unending_nightmare_target():
                    self.logger.warning("[Unending Nightmare] No target found to destroy.")
            try:
                self.duel_bot_client.wait_for_input_enabled()
            except Exception:
                pass
            self._unending_prompt_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[Unending Nightmare] Prompt handle failed: {e}")
            return False

    def play_turn(self):
        """Play Main Phase: repeatedly choose and execute best action until none or max iterations."""
        max_actions = 20
        actions_taken = 0
        failed_actions = set()
        self._log_board_state_detail()
        while actions_taken < max_actions:
            self._log_prompt_if_inputting()
            if self._handle_super_poly_discard_prompt():
                continue
            if self._handle_super_poly_fusion_prompt():
                continue
            if self._handle_super_poly_material_prompt():
                continue
            if self._handle_faceup_position_prompt():
                continue
            if self._handle_summon_zone_prompt():
                continue
            valid_raw = self._get_all_valid_actions()
            valid = self._filter_set_duplicates(valid_raw)
            valid = [a for a in valid if (a["card_name"], a["command_type"], a["index"], a["position"]) not in failed_actions]
            best = self._choose_best_action(valid)
            if best is None:
                if self.duel_bot_client.is_inputting():
                    if self._handle_super_poly_discard_prompt():
                        continue
                    if self._handle_super_poly_fusion_prompt():
                        continue
                    if self._handle_super_poly_material_prompt():
                        continue
                    if self._handle_faceup_position_prompt():
                        continue
                    if self._handle_summon_zone_prompt():
                        continue
                    if self._handle_unending_nightmare_prompt():
                        continue
                    self.logger.info("No action chosen (e.g. do not chain negate our own card) — cancel dialog.")
                    self.duel_bot_client.cancel_activation_prompts()
                    time.sleep(0.3)
                self.logger.info("No more playable actions. Ending turn.")
                break
            if self._execute_action(best) is False:
                failed_actions.add((best["card_name"], best["command_type"], best["index"], best["position"]))
                self.logger.warning(f"Action failed, blacklisting for this turn: {best['action_name']} on {best['card_name']}")
                continue
            if best["card_name"] == POT_OF_DUALITY_NAME:
                self._handle_pot_of_duality_dialog()
            elif best["card_name"] == POT_OF_EXTRAVAGANCE_NAME:
                self._handle_pot_of_extravagance_dialog()
            actions_taken += 1
            self.logger.info(f"Actions taken this turn: {actions_taken}")
            time.sleep(0.5)
            self._log_prompt_if_inputting()
            if self.duel_bot_client.cancel_activation_prompts():
                pass
        self.logger.info(f"Turn complete. Total actions: {actions_taken}")

    def handle_my_main_phase_1(self):
        self.duel_bot_client.cancel_activation_prompts()
        self.play_turn()
        turn = self.duel_bot_client.get_turn_number()
        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        if turn == 1:
            self.duel_bot_client.move_phase(Phase.End)
        else:
            # Before entering Battle, try to flip our face-down monsters (if allowed).
            self._try_flip_my_facedown_monsters()
            self.duel_bot_client.move_phase(Phase.Battle)

    def handle_my_main_phase_2(self):
        self.duel_bot_client.cancel_activation_prompts()
        self.play_turn()
        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        self.duel_bot_client.move_phase(Phase.End)

    def handle_my_battle_phase(self):
        """Battle Phase: attack automatically when possible."""
        self.logger.info("Handling battle phase...")
        self.duel_bot_client.handle_unexpected_prompts()

        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            opp_state = board.player_card_states.get(Player.Opponent)

            my_monsters = (my_state.monsters if my_state else []) or []
            opp_monsters = (opp_state.monsters if opp_state else []) or []

            opp_targets = []
            for om in opp_monsters:
                if om is None:
                    continue
                cid = getattr(om, "id", 0)
                if cid is None or cid == 0:
                    continue
                opp_targets.append(getattr(om, "position", None))

            # For each of our monsters, try to attack if game allows (CommandBit.Attack)
            for m in my_monsters:
                if m is None:
                    continue
                cid = getattr(m, "id", 0)
                if cid is None or cid == 0:
                    continue
                if getattr(m, "face", None) == CardFace.FaceDown:
                    continue
                if getattr(m, "turn", None) != CardTurn.Attack:
                    continue
                bits = getattr(m, "command_bits", []) or []
                if CommandBit.Attack not in bits:
                    self.logger.info(f"[Battle] Skip attack with {m.name} ({getattr(m, 'position', None)}) — no Attack command available.")
                    continue

                attacker_pos = getattr(m, "position", None)
                if attacker_pos is None:
                    continue

                # Prefer attacking opponent monster if any, else direct attack
                target_pos = None
                target_card = None
                for om in opp_monsters:
                    if om is None:
                        continue
                    tp = getattr(om, "position", None)
                    if tp is None:
                        continue
                    if tp in opp_targets:
                        target_pos = tp
                        target_card = om
                        break

                try:
                    # If opponent has face-up ATK higher than ours, do not attack into it (avoid suicide).
                    if target_card is not None:
                        my_atk = getattr(m, "attack", None)
                        if my_atk is None:
                            my_atk = getattr(m, "atk", None)
                        opp_atk = getattr(target_card, "attack", None)
                        if opp_atk is None:
                            opp_atk = getattr(target_card, "atk", None)
                        opp_turn = getattr(target_card, "turn", None)
                        if (
                            isinstance(my_atk, int)
                            and isinstance(opp_atk, int)
                            and my_atk < opp_atk
                            and opp_turn == CardTurn.Attack
                        ):
                            self.logger.info(
                                f"[Battle] Skip attack with {m.name} ({attacker_pos.name}) into stronger {target_card.name} "
                                f"(my ATK={my_atk} < opp ATK={opp_atk})."
                            )
                            raise RuntimeError("Skip suicidal attack")

                    if target_pos is None:
                        self.logger.info(f"[Battle] Direct attack with {m.name} ({attacker_pos.name})")
                        self.duel_bot_client.declare_attack(attacker_pos, None)
                    else:
                        self.logger.info(
                            f"[Battle] Attack {target_pos.name} with {m.name} ({attacker_pos.name})"
                        )
                        self.duel_bot_client.declare_attack(attacker_pos, target_pos)
                    self.duel_bot_client.wait_for_input_enabled()
                    self.duel_bot_client.handle_unexpected_prompts()
                    # Slightly longer delay between attacks so player can see animation.
                    time.sleep(0.8)
                    # In Battle: if game opens prompt after attack:
                    # - If chain top is our card -> cancel (do not activate our effect during attack).
                    # - If chain top is opponent's -> leave it so we can chain negate/respond.
                    # Always log prompt when present.
                    self._log_prompt_if_inputting()
                    if self.duel_bot_client.is_inputting():
                        top_player, is_monster_effect_chain, ctx_src = self._get_response_context()
                        if top_player != Player.Opponent:
                            self.logger.info("[Battle] Cancel own activation prompt during attack.")
                            self.duel_bot_client.cancel_activation_prompts()
                            time.sleep(0.2)
                except Exception as e:
                    self.logger.warning(f"[Battle] Attack failed for {m.name}: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"[Battle] Battle phase logic error: {e}")

        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        self.logger.info("Ending Battle -> Main Phase 2")
        self.duel_bot_client.move_phase(Phase.Main2)

    def handle_opponents_turn(self):
        """Opponent's turn: handle special dialogs, then if still prompting (chain?) try to chain negate by rules."""
        self.duel_bot_client.handle_unexpected_prompts()
        if self.duel_bot_client.is_inputting():
            self._log_prompt_if_inputting()
            # If at target-selection prompt for Infinite Impermanence (already activated),
            # try to auto-select target again to avoid stuck dialog.
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                last_used = ""
            if last_used == INFINITE_IMPERMANENCE_NAME:
                top_player, is_monster_effect_chain, ctx_src = self._get_response_context()
                if top_player == Player.Opponent and is_monster_effect_chain:
                    if self._provide_infinite_imperm_target():
                        self.duel_bot_client.wait_for_input_enabled()
                        if not self.duel_bot_client.is_inputting():
                            return
            if self._handle_super_poly_discard_prompt():
                return
            if self._handle_super_poly_material_prompt():
                return
            if self._handle_super_poly_fusion_prompt():
                return
            if self._handle_faceup_position_prompt():
                return
            if self._handle_summon_zone_prompt():
                return
            if self._try_activate_lancea_if_available():
                return
            valid_raw = self._get_all_valid_actions()
            valid = [a for a in valid_raw if a["command_type"] == CommandType.Action]
            valid = self._filter_set_duplicates(valid)
            best = self._choose_best_action(valid)
            if best:
                self.logger.info(f"[Opponent turn] Chain negate: {best['card_name']}")
                self._execute_action(best)
                if best["card_name"] == UNENDING_NIGHTMARE_NAME:
                    self._handle_unending_nightmare_prompt()
                self.duel_bot_client.wait_for_input_enabled()
            else:
                if self._handle_super_poly_discard_prompt():
                    return
                if self._handle_super_poly_material_prompt():
                    return
                if self._handle_faceup_position_prompt():
                    return
                if self._handle_summon_zone_prompt():
                    return
                self._handle_unending_nightmare_prompt()
                if self.duel_bot_client.is_inputting():
                    self.duel_bot_client.cancel_activation_prompts()
        self.duel_bot_client.cancel_activation_prompts()





if __name__ == "__main__":
    # Reset log file (truncate) on each run for easier reading from start
    import os
    _log_path = get_log_filename(__file__)
    if os.path.isfile(_log_path):
        with open(_log_path, "w", encoding="utf-8") as _f:
            _f.write("")
    logger_manager = LoggerManager(__file__)
    logger = logger_manager.get_logger()

    duel_bot_client = JDuelBotClient(master_duel_connection_address)
    duel_bot = LockdownStunBotHandler(duel_bot_client, logger)

    logger.info("Bot is running. Keep the game in foreground.")
    try:
        duel_bot.run()
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
