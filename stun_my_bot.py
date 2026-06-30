import sys
import time
from pathlib import Path

# Add project root to sys.path so jduel_bot package is importable from the venv
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

# ---------------------------------------------------------------------------
# Priority for choosing actions (higher = prefer earlier)
# ---------------------------------------------------------------------------
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
    "Macro Cosmos": 160,
    "Clockwork Night": 160,
    "There Can Be Only One": 155,
    "Necrovalley": 150,
    "Super Polymerization": 120,
    "Dimension Shifter": 115,
    "Artifact Lancea": 110,
    "Solemn Judgment": 105,
    "Solemn Strike": 104,
    "Solemn Warning": 103,
    "Iron Thunder": 102,
    "Dominus Impulse": 101,
    "Dominus Purge": 100,
    "Infinite Impermanence": 99,
    "Unending Nightmare": 95,
}

NEVER_SUMMON = {"Dimension Shifter", "Artifact Lancea"}
MONSTER_STUN_NAMES = {
    "Inspector Boarder", "Fossil Dyna Pachycephalo", "Thunder King Rai-Oh",
    "Barrier Statue of the Inferno", "Barrier Statue of the Torrent", "Banisher of the Radiance",
}
NEVER_SET_FROM_HAND = {"Artifact Lancea"}
SET_ALLOW_DUPLICATE_NAMES = {"Infinite Impermanence"}

LANCEA_NAME = "Artifact Lancea"
LANCEA_ANTI_BANISH_DECK_KEYWORDS = {
    "Kashtira", "Fenrir", "Unicorn", "Theosis", "Birth", "Riseheart", "Arise-Heart",
    "Runick", "Hugin", "Fountain", "Tip", "Munin",
    "Floowandereeze", "Robina", "Eaglen", "Empen", "Map", "Advent",
    "Rokket", "Borrel", "Striker Dragon", "Chaos Space", "Dragon Ravine", "Boot Sector",
    "Branded", "Aluber", "Fallen of Albaz", "Mirrorjade", "Lubellion", "Bystial",
}

NEGATE_TRAP_NAMES = {
    "Solemn Judgment", "Solemn Strike", "Solemn Warning",
    "Iron Thunder", "Dominus Impulse", "Dominus Purge", "Infinite Impermanence",
}
CONTINUOUS_TRAP_NAMES = {"Macro Cosmos", "There Can Be Only One", "Unending Nightmare"}
SOLEMN_NAMES = {"Solemn Judgment", "Solemn Strike", "Solemn Warning"}

MONSTER_ZONE_POSITION_MAX = 6
INFINITE_IMPERMANENCE_NAME = "Infinite Impermanence"
DOMINUS_IMPULSE_NAME = "Dominus Impulse"
CLOCKWORK_NIGHT_NAME = "Clockwork Night"
TCBOO_NAME = "There Can Be Only One"
DRAW_SPELL_NAMES = {"Pot of Duality", "Pot of Extravagance", "Pot of Desires"}
POT_OF_DUALITY_NAME = "Pot of Duality"
POT_OF_EXTRAVAGANCE_NAME = "Pot of Extravagance"
UNENDING_NIGHTMARE_NAME = "Unending Nightmare"
SUPER_POLY_NAME = "Super Polymerization"

# Coordinates for common prompts (1280x720)
# YES/NO generic dialog
_YES_COORD = Coordinates(741, 425)
_NO_COORD = Coordinates(541, 425)
# Coin toss: "Go First" (left button) / "Go Second" (right button) at 1280x720
# Adjust if the game layout differs; these are the standard positions.
_GO_FIRST_COORD = Coordinates(400, 490)
_GO_SECOND_COORD = Coordinates(880, 490)


class LockdownStunBotHandler(JDuelBotHandler):
    def __init__(self, duel_bot_client: JDuelBotClient, logger):
        super().__init__(duel_bot_client, logger)
        # Super Polymerization: multi-stage prompt tracking
        self._super_poly_cost_pending_until = 0.0
        self._super_poly_stage = "none"
        # Position prompt coordinates (Face-Up ATK/DEF)
        self._pos_faceup_atk = Coordinates(568, 580)
        self._pos_faceup_def = Coordinates(712, 580)
        # Unending Nightmare: only handle YES/NO prompt after activation
        self._unending_prompt_pending_until = 0.0
        # Track whether we tried to select Go First this non-duel window
        self._went_first: bool | None = None

    # ===== Non-duel phase: coin toss / deck selection =====
    def while_not_dueling(self):
        """
        Called every second when not in a duel.
        Attempt to click "Go First" whenever the game is waiting for input.
        This covers the coin-toss prompt that appears before each duel.
        """
        try:
            if self.duel_bot_client.is_inputting():
                self.logger.info("[Setup] Input prompt detected outside duel -> clicking 'Go First'")
                self.duel_bot_client.simulate_click(_GO_FIRST_COORD)
                time.sleep(0.5)
                # If still inputting, try cancel so the game doesn't get stuck
                if self.duel_bot_client.is_inputting():
                    self.duel_bot_client.cancel_activation_prompts()
        except Exception as e:
            self.logger.warning(f"[Setup] while_not_dueling error: {e}")
        self._went_first = None  # reset for next duel

    # ===== Draw phase =====
    def handle_my_draw_phase(self):
        """Override: log the turn, then let the base class draw."""
        try:
            turn = self.duel_bot_client.get_turn_number()
            self.logger.info(f"[Draw] Turn {turn}")
        except Exception:
            pass
        super().handle_my_draw_phase()

    # ===== Standby phase: surrender if we are going second =====
    def handle_my_standby_phase(self):
        """
        If it is turn 2 (our first turn, but the opponent went first on turn 1),
        surrender immediately. Going second with this stun strategy is losing.
        """
        try:
            turn = self.duel_bot_client.get_turn_number()
            if turn == 2:
                self.logger.warning("[Surrender] Opponent went first (turn 2 is our first turn). Surrendering.")
                self.duel_bot_client.surrender_duel()
                return
            self.logger.info(f"[Standby] Turn {turn} — we went first, continuing.")
        except Exception as e:
            self.logger.warning(f"[Standby] Error checking turn: {e}")
        super().handle_my_standby_phase()

    # ===== Get all valid actions from the game =====
    def _get_all_valid_actions(self):
        valid_actions = []
        try:
            board_state = self.duel_bot_client.get_board_state()
            my_state = board_state.player_card_states[Player.Myself]
        except Exception as e:
            self.logger.warning(f"[Actions] Failed to read board state: {e}")
            return valid_actions

        # Hand: Summon, Set, Action
        for i, card in enumerate(my_state.hand):
            if not card:
                continue
            atk_val = getattr(card, "attack", None)
            if atk_val is None:
                atk_val = getattr(card, "atk", 0) or 0
            for bit in (getattr(card, "command_bits", []) or []):
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

        # Field: monsters and spells_and_traps
        for zone, base_pos in (
            (my_state.monsters, CardPosition.Monster),
            (my_state.spells_and_traps, CardPosition.Magic),
        ):
            for i, card in enumerate(zone):
                if not card:
                    continue
                for bit in (getattr(card, "command_bits", []) or []):
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
        """Remove Set actions that would duplicate a card name on field (except Infinite Impermanence)."""
        try:
            board_state = self.duel_bot_client.get_board_state()
            my_state = board_state.player_card_states[Player.Myself]
        except Exception:
            return valid_actions
        names_on_field = {c.name for c in (my_state.spells_and_traps or []) if c}
        out = []
        for a in valid_actions:
            if a["command_type"] == CommandType.Set and a["position"] == CardPosition.Hand:
                if a["card_name"] in NEVER_SET_FROM_HAND:
                    continue
                card_type = str(a.get("type", "") or "")
                card_typeline = str(a.get("typeline", "") or "")
                is_spell = "Spell" in card_type or "Spell" in card_typeline
                is_field = "Field" in card_type or "Field" in card_typeline
                is_continuous = "Continuous" in card_type or "Continuous" in card_typeline
                if is_spell and not is_field and not is_continuous and a["card_name"] != SUPER_POLY_NAME:
                    continue
                if a["card_name"] in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME}:
                    conflict_present = any(
                        st and st.name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME} and st.name != a["card_name"]
                        for st in (my_state.spells_and_traps or [])
                    )
                    if conflict_present:
                        continue
                if a["card_name"] in names_on_field and a["card_name"] not in SET_ALLOW_DUPLICATE_NAMES:
                    continue
            out.append(a)
        return out

    def _opponent_is_anti_lancea_target(self) -> bool:
        try:
            board = self.duel_bot_client.get_board_state()
            opp = board.player_card_states.get(Player.Opponent)
            if not opp:
                return False
            seen: list[str] = []
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
                    return False
                self.logger.info("[Lancea] Activating from hand on opponent prompt")
                self.duel_bot_client.activate_monster_effect_from_hand(idx)
                self.duel_bot_client.wait_for_input_enabled()
                return True
        except Exception as e:
            self.logger.warning(f"[Lancea] Activation failed: {e}")
        return False

    def _pick_discard_index_for_cost(self) -> int | None:
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            if not my_state:
                return None
            best_idx = None
            best_score = None
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
                pass
            if last_used != SUPER_POLY_NAME:
                return False

            idx = self._pick_discard_index_for_cost()
            if idx is None:
                self.logger.warning("[Super Poly] No discard candidate; cancelling.")
                self.duel_bot_client.cancel_activation_prompts()
                self._super_poly_cost_pending_until = 0.0
                self._super_poly_stage = "none"
                return True

            candidates = list(dict.fromkeys([idx, 0, 1, 2, 3, 4, 5]))
            for cand in candidates:
                self.logger.info(f"[Super Poly] Discard cost: hand index={cand} (Middle)")
                try:
                    self.duel_bot_client.select_cards_from_dialog(
                        [CardSelection(card_index=cand)],
                        dialog_button_type=DialogButtonType.Middle,
                        milliseconds_delay_between_clicks=200,
                    )
                    self.duel_bot_client.wait_for_input_enabled()
                    if not self.duel_bot_client.is_inputting():
                        self._super_poly_cost_pending_until = 0.0
                        self._super_poly_stage = "none"
                        return True
                except Exception:
                    pass

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

            self.logger.info("[Super Poly] After discard still inputting -> materials stage")
            self._super_poly_stage = "materials"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Discard prompt failed: {e}")
            return False

    def _handle_super_poly_material_prompt(self) -> bool:
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
                pass
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

            candidates = collect(opp, True) + collect(opp, False)
            if len(set(candidates)) < 2:
                candidates += collect(my, False)

            uniq = list(dict.fromkeys(candidates))
            if len(uniq) < 2:
                self.logger.warning("[Super Poly] Not enough monsters; cancelling.")
                self.duel_bot_client.cancel_activation_prompts()
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            p1, p2 = uniq[0], uniq[1]
            self.logger.info(f"[Super Poly] Fusion materials: {p1.name}, {p2.name}")
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
            try:
                self.duel_bot_client.execute_command(Player.Myself, CardPosition.Select, 0, CommandType.Decide)
                self.duel_bot_client.wait_for_input_enabled()
            except Exception:
                pass

            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            self.logger.info("[Super Poly] After materials still inputting -> fusion stage")
            self._super_poly_stage = "fusion"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Material prompt failed: {e}")
            return False

    def _handle_faceup_position_prompt(self) -> bool:
        try:
            if not self.duel_bot_client.is_inputting():
                return False
            if getattr(self, "_super_poly_stage", "none") != "position":
                return False
            if time.time() > float(self._super_poly_cost_pending_until or 0.0):
                self._super_poly_stage = "none"
                return False
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                pass
            if last_used != SUPER_POLY_NAME:
                return False

            self.logger.info("[Super Poly] Position prompt -> Face-Up Attack")
            self.duel_bot_client.simulate_click(self._pos_faceup_atk)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "zone"
                self._super_poly_cost_pending_until = time.time() + 8.0
                return True

            self.logger.info("[Super Poly] Position prompt -> trying Face-Up Defense")
            self.duel_bot_client.simulate_click(self._pos_faceup_def)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "zone"
                self._super_poly_cost_pending_until = time.time() + 8.0
                return True

            self.logger.warning("[Super Poly] Position prompt still inputting -> cancelling")
            self.duel_bot_client.cancel_activation_prompts()
            self._super_poly_stage = "none"
            self._super_poly_cost_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Position prompt failed: {e}")
            return False

    def _handle_summon_zone_prompt(self) -> bool:
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
                self.logger.warning("[Super Poly] No free monster zone for summon.")
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True
            self.logger.info(f"[Super Poly] Summon zone -> {pos.name}")
            self.duel_bot_client.click_my_monster_zone(pos)
            time.sleep(0.4)
            self.duel_bot_client.wait_for_input_enabled()
            self._super_poly_stage = "none"
            self._super_poly_cost_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Summon zone prompt failed: {e}")
            return False

    def _handle_super_poly_fusion_prompt(self) -> bool:
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
                pass
            if last_used != SUPER_POLY_NAME:
                return False

            time.sleep(0.3)
            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            self.logger.info("[Super Poly] Fusion prompt -> selecting index=0")
            try:
                self.duel_bot_client.select_card_from_dialog(
                    CardSelection(card_index=0),
                    dialog_button_type=DialogButtonType.Middle,
                    milliseconds_delay_between_clicks=200,
                )
                self.duel_bot_client.wait_for_input_enabled()
            except Exception as e:
                self.logger.warning(f"[Super Poly] Fusion select failed: {e}")

            if not self.duel_bot_client.is_inputting():
                self._super_poly_stage = "none"
                self._super_poly_cost_pending_until = 0.0
                return True

            self.logger.info("[Super Poly] After fusion still inputting -> position stage")
            self._super_poly_stage = "position"
            self._super_poly_cost_pending_until = time.time() + 12.0
            return True
        except Exception as e:
            self.logger.warning(f"[Super Poly] Fusion prompt failed: {e}")
            return False

    def _try_flip_my_facedown_monsters(self) -> None:
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            for m in (my_state.monsters if my_state else []) or []:
                if not m or getattr(m, "face", None) != CardFace.FaceDown:
                    continue
                pos = getattr(m, "position", None)
                if pos is None:
                    continue
                bits = getattr(m, "command_bits", []) or []
                if CommandBit.Reverse not in bits:
                    continue
                try:
                    self.logger.info(f"[Flip] Flip summon {m.name} ({pos.name})")
                    self.duel_bot_client.perform_flip_summon(pos)
                    self.duel_bot_client.handle_unexpected_prompts()
                    time.sleep(0.2)
                except Exception as e:
                    self.logger.warning(f"[Flip] Failed for {m.name}: {e}")
        except Exception as e:
            self.logger.warning(f"[Flip] Scan failed: {e}")

    def _infer_last_used_owner_and_type(self, last_used: str):
        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            opp_state = board.player_card_states.get(Player.Opponent)

            def scan(state, player: Player):
                if not state:
                    return None
                for c in state.monsters or []:
                    if c and str(c.name) == last_used:
                        return player, True
                for c in state.spells_and_traps or []:
                    if c and str(c.name) == last_used:
                        return player, False
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
            pass

        if last_used:
            inferred_player, inferred_is_monster = self._infer_last_used_owner_and_type(last_used)
            if (inferred_player is not None
                    and (top_player is None or top_player == Player.Myself)
                    and inferred_player == Player.Opponent):
                top_player = Player.Opponent
                is_monster_effect = inferred_is_monster
                source = f"last_used:{last_used}"
            if top_player is None and inferred_player is not None:
                top_player = inferred_player
                is_monster_effect = inferred_is_monster
                source = f"last_used:{last_used}"

        return top_player, is_monster_effect, source

    def _choose_best_action(self, valid_actions):
        if not valid_actions:
            return None
        try:
            board_state = self.duel_bot_client.get_board_state()
            my_state = board_state.player_card_states[Player.Myself]
            opp_state = board_state.player_card_states.get(Player.Opponent)
        except Exception:
            return None
        top_player, is_monster_effect_chain, ctx_src = self._get_response_context()
        if top_player is not None:
            self.logger.info(f"[Chain] top={top_player} monster_effect={is_monster_effect_chain} (src={ctx_src})")

        best = None
        best_score = -1

        for action in valid_actions:
            card_name = action["card_name"]
            cmd = action["command_type"]
            pos = action["position"]

            # From hand: only Summon, Action, Set
            if pos == CardPosition.Hand and cmd not in (CommandType.Summon, CommandType.Action, CommandType.Set):
                continue
            if cmd == CommandType.Summon and card_name in NEVER_SUMMON:
                continue
            # From field: only Action and TurnAtk
            if pos != CardPosition.Hand and cmd not in (CommandType.Action, CommandType.TurnAtk):
                continue

            if pos == CardPosition.Hand and cmd == CommandType.Summon:
                atk_val = int(action.get("attack", 0) or 0)
                try:
                    turn_num = self.duel_bot_client.get_turn_number()
                except Exception:
                    turn_num = 2
                if turn_num == 1:
                    base_priority = (400 + HAND_PRIORITY.get(card_name, 0)
                                     if card_name in MONSTER_STUN_NAMES
                                     else 300 + atk_val)
                else:
                    base_priority = 300 + atk_val
            elif cmd == CommandType.TurnAtk:
                base_priority = 250
            else:
                base_priority = HAND_PRIORITY.get(card_name, 10)

            # Skip Mudragon effect
            if cmd == CommandType.Action and card_name == "Mudragon of the Swamp":
                continue

            # Super Poly: only when opponent has >=2 monsters
            if cmd == CommandType.Action and card_name == SUPER_POLY_NAME:
                opp_monster_count = sum(
                    1 for m in (opp_state.monsters or []) if m and getattr(m, "position", None) is not None
                ) if opp_state else 0
                if opp_monster_count < 2:
                    self.logger.info(f"[Super Poly] Skip — opponent monsters={opp_monster_count}")
                    continue

            # Artifact Lancea: never set; only chain-activate vs banish decks
            if pos == CardPosition.Hand and card_name == LANCEA_NAME:
                if cmd == CommandType.Set:
                    continue
                if cmd == CommandType.Action:
                    if top_player != Player.Opponent:
                        continue
                    if not self._opponent_is_anti_lancea_target():
                        self.logger.info("[Lancea] Skip — not banish-deck matchup")
                        continue
                    base_priority = 700

            # Dimension Shifter: early activation preferred
            if pos == CardPosition.Hand and card_name == "Dimension Shifter" and cmd == CommandType.Action:
                base_priority = 750

            # Clockwork Night / TCBOO conflict guard
            if card_name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME}:
                conflict = any(
                    st and st.name in {CLOCKWORK_NIGHT_NAME, TCBOO_NAME} and st.name != card_name
                    for st in (my_state.spells_and_traps or [])
                )
                if conflict:
                    self.logger.info(f"[Conflict] Skip '{card_name}' — other conflict card on field")
                    continue

            # No second copy of Clockwork Night / Time-Tearing Morganite on field
            if pos == CardPosition.Hand and cmd == CommandType.Action and card_name in {CLOCKWORK_NIGHT_NAME, "Time-Tearing Morganite"}:
                if any(c and c.name == card_name for c in (my_state.spells_and_traps or [])):
                    self.logger.info(f"[Spell] Skip '{card_name}' — already on field")
                    continue

            # Draw spells: boost priority when no chain
            if top_player is None and cmd == CommandType.Action and card_name in DRAW_SPELL_NAMES:
                base_priority += 100

            # Unending Nightmare: only activate when opponent has face-up S/T
            if cmd == CommandType.Action and card_name == UNENDING_NIGHTMARE_NAME:
                if not self._has_opponent_faceup_spell_trap():
                    self.logger.info("[Unending Nightmare] Skip — no face-up S/T target")
                    continue

            # Chain negate logic
            if cmd == CommandType.Action and card_name in NEGATE_TRAP_NAMES:
                if top_player == Player.Myself:
                    self.logger.info(f"[Negate] Skip '{card_name}' — chaining own card")
                    continue
                if top_player is None:
                    self.logger.info(f"[Negate] Skip '{card_name}' — no opponent chain")
                    continue
                if top_player == Player.Opponent:
                    if card_name in SOLEMN_NAMES:
                        base_priority = 1000
                    elif card_name == INFINITE_IMPERMANENCE_NAME:
                        if not is_monster_effect_chain:
                            self.logger.info("[Negate] Skip Impermanence — not monster effect")
                            continue
                        has_target = opp_state and any(
                            m and getattr(m, "position", None) is not None
                            for m in (opp_state.monsters or [])
                        )
                        if not has_target:
                            self.logger.info("[Negate] Skip Impermanence — no monster target")
                            continue
                        base_priority = 500
                    elif card_name == DOMINUS_IMPULSE_NAME:
                        base_priority = 600
                    else:
                        base_priority = max(base_priority, 400)

            # Continuous traps: lower priority when chaining opponent
            if cmd == CommandType.Action and card_name in CONTINUOUS_TRAP_NAMES and top_player == Player.Opponent:
                if card_name == UNENDING_NIGHTMARE_NAME and self._has_opponent_faceup_spell_trap():
                    base_priority = max(base_priority, 200)
                else:
                    base_priority = min(base_priority, 50)
                    self.logger.info(f"[Continuous] '{card_name}' priority lowered to 50")

            if base_priority > best_score:
                best_score = base_priority
                best = action

        return best

    def _provide_infinite_imperm_target(self) -> bool:
        try:
            try:
                chain_data = self.duel_bot_client.get_chain_data()
            except Exception:
                chain_data = []

            if chain_data:
                top = chain_data[-1]
                top_player = getattr(top, "player", None)
                top_pos = getattr(top, "position", None)
                if top_player == Player.Opponent and top_pos is not None:
                    if 0 <= int(top_pos) <= MONSTER_ZONE_POSITION_MAX:
                        self.logger.info(f"[II] Target (chain): {top_pos.name}")
                        self.duel_bot_client.target_card(Player.Opponent, top_pos)
                        time.sleep(0.4)
                        return True

            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False
            faceup_mon = any_mon = None
            for m in opp_state.monsters or []:
                if not m or getattr(m, "position", None) is None:
                    continue
                any_mon = any_mon or m
                if getattr(m, "face", None) == CardFace.FaceUp:
                    faceup_mon = faceup_mon or m
            target = faceup_mon or any_mon
            if not target:
                return False
            self.logger.info(f"[II] Target (fallback): {target.name} ({target.position.name})")
            self.duel_bot_client.target_card(Player.Opponent, target.position)
            time.sleep(0.4)
            return True
        except Exception as e:
            self.logger.warning(f"[II] Target failed: {e}")
            return False

    def _execute_action(self, action):
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
                        self.logger.warning("No free monster zone.")
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
                        self.logger.warning("No free S/T zone.")
                        return False
                    self.logger.info(f"Setting '{card_name}' face-down to {st_zone.name}")
                    self.duel_bot_client.execute_command(Player.Myself, CardPosition.Hand, idx, CommandType.Set)
                    self.duel_bot_client.wait_for_input_enabled()
                    self.duel_bot_client.execute_command(Player.Myself, st_zone, 0, CommandType.Decide)
                    self.duel_bot_client.wait_for_input_enabled()

                elif cmd == CommandType.Action:
                    card_type = action.get("type", "") or ""
                    card_typeline = action.get("typeline", "") or ""
                    is_monster = "Monster" in card_type or "Monster" in card_typeline
                    if is_monster:
                        self.logger.info(f"Monster effect from hand: '{card_name}'")
                        self.duel_bot_client.activate_monster_effect_from_hand(idx)
                        self.duel_bot_client.wait_for_input_enabled()
                        return True
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
                        self._super_poly_cost_pending_until = time.time() + 12.0
                        self._super_poly_stage = "discard"
                    self.duel_bot_client.wait_for_input_enabled()
                else:
                    return False

            else:
                if cmd == CommandType.Action:
                    self.duel_bot_client.activate_spell_or_trap_from_field(pos)
                    if card_name == UNENDING_NIGHTMARE_NAME:
                        self._unending_prompt_pending_until = time.time() + 8.0
                    if card_name == SUPER_POLY_NAME:
                        self._super_poly_cost_pending_until = time.time() + 12.0
                        self._super_poly_stage = "discard"
                    self.duel_bot_client.wait_for_input_enabled()
                    if card_name == INFINITE_IMPERMANENCE_NAME and self.duel_bot_client.is_inputting():
                        self._provide_infinite_imperm_target()
                        self.duel_bot_client.wait_for_input_enabled()
                elif cmd == CommandType.TurnAtk:
                    self.logger.info(f"Switch DEF->ATK: '{card_name}' ({pos.name})")
                    self.duel_bot_client.turn_attack(pos)
                    self.duel_bot_client.wait_for_input_enabled()
                else:
                    return False
            return True
        except Exception as e:
            self.logger.warning(f"Execute action failed: {e}")
            return False

    def _log_board_state_detail(self):
        try:
            board = self.duel_bot_client.get_board_state()
            for player in (Player.Myself, Player.Opponent):
                label = "Me" if player == Player.Myself else "Opp"
                state = board.player_card_states.get(player)
                if not state:
                    continue
                hand_names = [c.name if c else "?" for c in state.hand]
                self.logger.info(f"[Board] {label} Hand({len(hand_names)}): {hand_names}")
                for i, c in enumerate(state.monsters or []):
                    if c:
                        self.logger.info(f"[Board]   {label} M[{i}]: {c.name} face={getattr(c,'face','?')} turn={getattr(c,'turn','?')}")
                for i, c in enumerate(state.spells_and_traps or []):
                    if c:
                        self.logger.info(f"[Board]   {label} ST[{i}]: {c.name} face={getattr(c,'face','?')}")
        except Exception as e:
            self.logger.warning(f"[Board] Log failed: {e}")

    def _log_prompt_if_inputting(self):
        try:
            if not self.duel_bot_client.is_inputting():
                return
            last_used = ""
            try:
                last_used = self.duel_bot_client.get_last_used_card_name()
            except Exception:
                pass
            top_player, is_monster, src = self._get_response_context()
            self.logger.info(
                f"[Prompt] inputting=True last='{last_used}' chain_top={top_player} "
                f"monster={is_monster} (src={src}) sp_stage={getattr(self,'_super_poly_stage','none')}"
            )
        except Exception as e:
            self.logger.warning(f"[Prompt] Log failed: {e}")

    def _handle_pot_of_duality_dialog(self):
        try:
            if not self.duel_bot_client.is_inputting():
                return
            time.sleep(0.4)
            if not self.duel_bot_client.is_inputting():
                return
            cards = self.duel_bot_client.get_dialog_card_list()
            if len(cards) != 3:
                self.logger.warning(f"[PoD] Unexpected card count: {len(cards)}")
                return
            best = max(cards, key=lambda c: HAND_PRIORITY.get(str(c), 0))
            idx = cards.index(best) if best in cards else 0
            self.logger.info(f"[PoD] Pick '{best}' (index={idx})")
            self.duel_bot_client.select_card_from_dialog(
                CardSelection(card_index=idx),
                dialog_button_type=DialogButtonType.Middle,
                milliseconds_delay_between_clicks=200,
            )
            self.duel_bot_client.wait_for_input_enabled()
        except Exception as e:
            self.logger.warning(f"[PoD] Dialog failed: {e}")
            try:
                self.duel_bot_client.cancel_activation_prompts()
            except Exception:
                pass

    def _handle_pot_of_extravagance_dialog(self):
        try:
            if not self.duel_bot_client.is_inputting():
                return
            time.sleep(0.4)
            if not self.duel_bot_client.is_inputting():
                return
            six_option = Coordinates(610, 320)
            ok_button = Coordinates(640, 540)
            self.logger.info("[PoE] Clicking 6 cards option")
            self.duel_bot_client.simulate_click(six_option)
            time.sleep(0.2)
            self.duel_bot_client.simulate_click(ok_button)
            self.duel_bot_client.wait_for_input_enabled()
            if self.duel_bot_client.is_inputting():
                self.logger.warning("[PoE] Still inputting -> cancelling")
                self.duel_bot_client.cancel_activation_prompts()
        except Exception as e:
            self.logger.warning(f"[PoE] Dialog failed: {e}")
            try:
                self.duel_bot_client.cancel_activation_prompts()
            except Exception:
                pass

    def _has_opponent_faceup_spell_trap(self):
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
        try:
            opp_state = self.duel_bot_client.get_board_state().player_card_states.get(Player.Opponent)
            if not opp_state:
                return False
            for st in opp_state.spells_and_traps or []:
                if not st or st.face != CardFace.FaceUp:
                    continue
                self.logger.info(f"[UN] Target: {st.name} ({st.position.name})")
                self.duel_bot_client.target_card(Player.Opponent, st.position)
                time.sleep(1.0)
                return True
            if opp_state.field_spell and opp_state.field_spell.face == CardFace.FaceUp:
                self.logger.info(f"[UN] Target Field: {opp_state.field_spell.name}")
                self.duel_bot_client.target_card(Player.Opponent, CardPosition.Field)
                time.sleep(1.0)
                return True
        except Exception as e:
            self.logger.warning(f"[UN] Target failed: {e}")
        return False

    def _handle_unending_nightmare_prompt(self) -> bool:
        try:
            if not self.duel_bot_client.is_inputting():
                return False
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
            if not has_target:
                self.logger.info("[UN] Cancel (no face-up S/T)")
                try:
                    self.duel_bot_client.cancel_activation_prompts()
                    self.duel_bot_client.wait_for_input_enabled()
                except Exception:
                    pass
                self._unending_prompt_pending_until = 0.0
                return True

            self.logger.info("[UN] YES then select target")
            try:
                self.duel_bot_client.simulate_click(_YES_COORD)
                self.duel_bot_client.wait_for_input_enabled()
                time.sleep(0.3)
            except Exception:
                pass
            if self.duel_bot_client.is_inputting():
                if not self._provide_unending_nightmare_target():
                    self.logger.warning("[UN] No target found.")
            try:
                self.duel_bot_client.wait_for_input_enabled()
            except Exception:
                pass
            self._unending_prompt_pending_until = 0.0
            return True
        except Exception as e:
            self.logger.warning(f"[UN] Prompt failed: {e}")
            return False

    # ===== Main turn logic =====

    def play_turn(self):
        """
        Repeatedly choose and execute the best available action until none remain
        or the safety cap is reached. Each iteration refreshes board state so that
        newly available actions (e.g. setting a trap after summoning a monster)
        are always considered.
        """
        max_actions = 30
        actions_taken = 0
        failed_actions: set = set()
        consecutive_no_action = 0

        self._log_board_state_detail()

        while actions_taken < max_actions:
            # --- Handle any pending multi-step prompts first ---
            handled_prompt = (
                self._handle_super_poly_discard_prompt()
                or self._handle_super_poly_fusion_prompt()
                or self._handle_super_poly_material_prompt()
                or self._handle_faceup_position_prompt()
                or self._handle_summon_zone_prompt()
            )
            if handled_prompt:
                consecutive_no_action = 0
                continue

            self._log_prompt_if_inputting()

            # --- Collect available actions ---
            try:
                valid_raw = self._get_all_valid_actions()
            except Exception as e:
                self.logger.warning(f"[Turn] get_all_valid_actions error: {e}")
                time.sleep(0.5)
                continue

            valid = self._filter_set_duplicates(valid_raw)
            valid = [
                a for a in valid
                if (a["card_name"], a["command_type"], a["index"], a["position"]) not in failed_actions
            ]

            best = self._choose_best_action(valid)

            if best is None:
                # No action chosen — handle any remaining prompts then break
                if self.duel_bot_client.is_inputting():
                    handled = (
                        self._handle_super_poly_discard_prompt()
                        or self._handle_super_poly_fusion_prompt()
                        or self._handle_super_poly_material_prompt()
                        or self._handle_faceup_position_prompt()
                        or self._handle_summon_zone_prompt()
                        or self._handle_unending_nightmare_prompt()
                    )
                    if handled:
                        consecutive_no_action = 0
                        continue
                    self.logger.info("[Turn] No action — cancelling dialog.")
                    self.duel_bot_client.cancel_activation_prompts()
                    time.sleep(0.3)

                consecutive_no_action += 1
                if consecutive_no_action >= 2:
                    self.logger.info("[Turn] No more playable actions. Ending turn.")
                    break
                # Give the game one more chance to present new options
                time.sleep(0.4)
                continue

            consecutive_no_action = 0

            if self._execute_action(best) is False:
                failed_actions.add((best["card_name"], best["command_type"], best["index"], best["position"]))
                self.logger.warning(f"[Turn] Action failed, blacklisting: {best['action_name']} on {best['card_name']}")
                continue

            # Handle post-activation dialogs immediately
            if best["card_name"] == POT_OF_DUALITY_NAME:
                self._handle_pot_of_duality_dialog()
            elif best["card_name"] == POT_OF_EXTRAVAGANCE_NAME:
                self._handle_pot_of_extravagance_dialog()

            actions_taken += 1
            self.logger.info(f"[Turn] Actions taken: {actions_taken}")

            # Brief pause to let animations finish before querying the board again
            time.sleep(0.4)
            self._log_prompt_if_inputting()

            # Only cancel lingering activation prompts — not the turn itself
            if self.duel_bot_client.is_inputting():
                top_player, _, _ = self._get_response_context()
                if top_player != Player.Opponent:
                    self.duel_bot_client.cancel_activation_prompts()

        self.logger.info(f"[Turn] Complete. Total actions: {actions_taken}")

    def handle_my_main_phase_1(self):
        self.duel_bot_client.cancel_activation_prompts()
        self.play_turn()
        turn = self.duel_bot_client.get_turn_number()
        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        if turn == 1:
            self.duel_bot_client.move_phase(Phase.End)
        else:
            self._try_flip_my_facedown_monsters()
            self.duel_bot_client.move_phase(Phase.Battle)

    def handle_my_main_phase_2(self):
        self.duel_bot_client.cancel_activation_prompts()
        self.play_turn()
        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        self.duel_bot_client.move_phase(Phase.End)

    def handle_my_battle_phase(self):
        self.logger.info("[Battle] Starting...")
        self.duel_bot_client.handle_unexpected_prompts()

        try:
            board = self.duel_bot_client.get_board_state()
            my_state = board.player_card_states.get(Player.Myself)
            opp_state = board.player_card_states.get(Player.Opponent)
            my_monsters = (my_state.monsters if my_state else []) or []
            opp_monsters = (opp_state.monsters if opp_state else []) or []

            opp_targets = [
                getattr(om, "position", None)
                for om in opp_monsters
                if om is not None and (getattr(om, "id", 0) or 0) != 0
            ]

            for m in my_monsters:
                if m is None or (getattr(m, "id", 0) or 0) == 0:
                    continue
                if getattr(m, "face", None) == CardFace.FaceDown:
                    continue
                if getattr(m, "turn", None) != CardTurn.Attack:
                    continue
                if CommandBit.Attack not in (getattr(m, "command_bits", []) or []):
                    self.logger.info(f"[Battle] Skip {m.name} — no Attack command")
                    continue

                attacker_pos = getattr(m, "position", None)
                if attacker_pos is None:
                    continue

                target_pos = None
                target_card = None
                for om in opp_monsters:
                    if om is None:
                        continue
                    tp = getattr(om, "position", None)
                    if tp is not None and tp in opp_targets:
                        target_pos = tp
                        target_card = om
                        break

                try:
                    if target_card is not None:
                        my_atk = getattr(m, "attack", None) or getattr(m, "atk", None)
                        opp_atk = getattr(target_card, "attack", None) or getattr(target_card, "atk", None)
                        opp_turn = getattr(target_card, "turn", None)
                        if (isinstance(my_atk, int) and isinstance(opp_atk, int)
                                and my_atk < opp_atk and opp_turn == CardTurn.Attack):
                            self.logger.info(
                                f"[Battle] Skip suicide attack {m.name} ({my_atk}) vs {target_card.name} ({opp_atk})"
                            )
                            continue

                    if target_pos is None:
                        self.logger.info(f"[Battle] Direct attack with {m.name}")
                        self.duel_bot_client.declare_attack(attacker_pos, None)
                    else:
                        self.logger.info(f"[Battle] Attack {target_pos.name} with {m.name}")
                        self.duel_bot_client.declare_attack(attacker_pos, target_pos)

                    self.duel_bot_client.wait_for_input_enabled()
                    self.duel_bot_client.handle_unexpected_prompts()
                    time.sleep(0.8)
                    self._log_prompt_if_inputting()

                    if self.duel_bot_client.is_inputting():
                        top_player, _, _ = self._get_response_context()
                        if top_player != Player.Opponent:
                            self.logger.info("[Battle] Cancel own prompt during attack")
                            self.duel_bot_client.cancel_activation_prompts()
                            time.sleep(0.2)

                except Exception as e:
                    self.logger.warning(f"[Battle] Attack failed for {m.name}: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"[Battle] Phase error: {e}")

        self.duel_bot_client.cancel_activation_prompts()
        time.sleep(0.3)
        self.logger.info("[Battle] -> Main Phase 2")
        self.duel_bot_client.move_phase(Phase.Main2)

    def handle_opponents_turn(self):
        """Opponent's turn: handle special dialogs and chain-negate when appropriate."""
        self.duel_bot_client.handle_unexpected_prompts()
        if not self.duel_bot_client.is_inputting():
            self.duel_bot_client.cancel_activation_prompts()
            return

        self._log_prompt_if_inputting()

        # Re-target Infinite Impermanence if already activated
        try:
            last_used = self.duel_bot_client.get_last_used_card_name()
        except Exception:
            last_used = ""
        if last_used == INFINITE_IMPERMANENCE_NAME:
            top_player, is_monster, _ = self._get_response_context()
            if top_player == Player.Opponent and is_monster:
                if self._provide_infinite_imperm_target():
                    self.duel_bot_client.wait_for_input_enabled()
                    if not self.duel_bot_client.is_inputting():
                        return

        # Multi-stage Super Poly prompts
        if (self._handle_super_poly_discard_prompt()
                or self._handle_super_poly_material_prompt()
                or self._handle_super_poly_fusion_prompt()
                or self._handle_faceup_position_prompt()
                or self._handle_summon_zone_prompt()):
            return

        # Lancea vs banish decks
        if self._try_activate_lancea_if_available():
            return

        # Chain negate: only Action commands on opponent's turn
        try:
            valid_raw = self._get_all_valid_actions()
        except Exception:
            valid_raw = []
        valid = [a for a in valid_raw if a["command_type"] == CommandType.Action]
        valid = self._filter_set_duplicates(valid)
        best = self._choose_best_action(valid)

        if best:
            self.logger.info(f"[OppTurn] Chain negate: {best['card_name']}")
            self._execute_action(best)
            if best["card_name"] == UNENDING_NIGHTMARE_NAME:
                self._handle_unending_nightmare_prompt()
            self.duel_bot_client.wait_for_input_enabled()
        else:
            if (self._handle_super_poly_discard_prompt()
                    or self._handle_super_poly_material_prompt()
                    or self._handle_faceup_position_prompt()
                    or self._handle_summon_zone_prompt()):
                return
            self._handle_unending_nightmare_prompt()
            if self.duel_bot_client.is_inputting():
                self.duel_bot_client.cancel_activation_prompts()

        self.duel_bot_client.cancel_activation_prompts()


if __name__ == "__main__":
    import os
    _log_path = get_log_filename(__file__)
    if os.path.isfile(_log_path):
        with open(_log_path, "w", encoding="utf-8") as _f:
            _f.write("")

    logger_manager = LoggerManager(__file__)
    logger = logger_manager.get_logger()

    duel_bot_client = JDuelBotClient(master_duel_connection_address)
    duel_bot = LockdownStunBotHandler(duel_bot_client, logger)

    logger.info("Stun bot running. Press Ctrl+C to stop.")
    try:
        duel_bot.run()
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
