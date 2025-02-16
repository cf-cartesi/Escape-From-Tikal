from logging import getLogger, basicConfig, DEBUG
from pydantic import BaseModel
from typing import Annotated, List
import json
import jsonpickle

from cartesi import App, Rollup, RollupData, abi
from cartesi.models import _str2hex as str2hex

from game_engine.core_engine.const import EXIT
from game_engine.core_engine import tikal_core as tkl_core
from game_engine.core_engine.confs import STANDARD_LLAMA_PAYLOAD


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)
app = App(raw_input = True)

BytesList = Annotated[List[bytes], abi.ABIType('bytes[]')]

class Words(BaseModel):
    challenge_id: abi.Bytes32
    words: BytesList

class ChallengeNotice(BaseModel):
    challenge_id: abi.Bytes32
    timestamp: abi.UInt256
    score: abi.UInt256
    n_moves: abi.UInt256
    n_moves_left: abi.UInt256
    user: abi.Address
    n_treasures: abi.UInt8
    escaped: abi.Bool

LLAMA_DOMAIN = int.from_bytes(bytes.fromhex('2b'), "big") # llama domain
DATA_MESSAGE = "The word is \"%s\" and the word sets are:\n%s"



@app.advance()
def handle_advance(rollup: Rollup, data: RollupData) -> bool:
    LOGGER.debug(f"App advance 0x{rollup=} {data=}")

    payload = data.bytes_payload()
    words_model = abi.decode_to_model(data=payload, model=Words)

    selected_words = [w.decode('utf-8') for w in words_model.words]

    LOGGER.info(f"Challenge id 0x{words_model.challenge_id.hex().rjust(64,'0')} and words selected {selected_words}")

    def call_llama_server_gio(message):
        llama_message = STANDARD_LLAMA_PAYLOAD.copy()
        llama_message["messages"][1]["content"] = message

        LOGGER.info(message)
        llama_message["messages"][1]["content"] = message

        res = rollup.gio(
            {
                "domain":LLAMA_DOMAIN,
                "id":str2hex(json.dumps(llama_message))
            }
        )
        if res is None: raise Exception("No gio response")
        gio_res = json.loads(res.decode("utf-8"))
        llama_res = None
        if gio_res.get('response') is not None:
            llama_res = json.loads(bytes.fromhex(gio_res['response'][2:]).decode("utf-8"))
        LOGGER.debug(f"llama Res {llama_res}")

        if llama_res is not None and llama_res.get('choices') is not None and len(llama_res['choices']) > 0 and \
                llama_res['choices'][0].get('message') is not None and  llama_res['choices'][0]['message'].get('content') is not None:
            content = llama_res['choices'][0]['message']['content']
            return content

        return ""

    int_game_id = int.from_bytes(words_model.challenge_id, "big")
    new_game_state = tkl_core.GameState(game_id=int_game_id, new_game=True)

    #Removing some indexes to make the response simpler
    if new_game_state.game_board is not None:
        del new_game_state.game_board.words_on_board
        del new_game_state.game_board.word_tile_coords_set

    serialized_output_state = jsonpickle.encode(new_game_state)

    for selected_word in selected_words:
        deserialized_state = jsonpickle.decode(serialized_output_state)
        current_game_state = tkl_core.GameState(game_map=deserialized_state.game_map,
            game_board=deserialized_state.game_board,
            words=deserialized_state.words,
            game_id=deserialized_state.game_id,
            new_game=False)

        #Create game executor and load map and board
        game_executor = tkl_core.GameExecutor(current_game_state.game_board, current_game_state.game_map)

        #Execute game
        gameboard_output = game_executor.execute_game(current_game_state.words, handler=call_llama_server_gio)

        #Remove indexes
        if gameboard_output is not None:
            del gameboard_output.words_on_board
            del gameboard_output.word_tile_coords_set

        current_game_state.game_board = gameboard_output
        serialized_output_state = jsonpickle.encode(current_game_state)


    deserialized_state = jsonpickle.decode(serialized_output_state)
    final_game_state = tkl_core.GameState(game_map=deserialized_state.game_map,
        game_board=deserialized_state.game_board,
        words=deserialized_state.words,
        game_id=deserialized_state.game_id,
        new_game=False)

    if (data.metadata  is not None):
        notice: ChallengeNotice
        if (final_game_state.game_board is not None):
            notice = ChallengeNotice(
                challenge_id = words_model.challenge_id,
                timestamp = data.metadata.block_timestamp,
                score = final_game_state.game_board.score,
                n_moves = final_game_state.game_board.move_count,
                n_moves_left = final_game_state.game_board.water_supply,
                user = data.metadata.msg_sender,
                n_treasures = final_game_state.game_board.treasure_count,
                escaped = final_game_state.game_board.last_visited_tile_type == EXIT,
            )
        else:
            notice = ChallengeNotice(
                challenge_id = words_model.challenge_id,
                timestamp = data.metadata.block_timestamp,
                score = 0,
                n_moves = 0,
                n_moves_left =0,
                user = data.metadata.msg_sender,
                n_treasures = 0,
                escaped = False,
            )
        notice_hex = f"0x{abi.encode_model(notice).hex()}"
        LOGGER.debug(f"{notice=}")
        LOGGER.debug(f"{notice_hex=}")
        rollup.notice(notice_hex)
    return True


@app.inspect()
def handle_inspect(rollup: Rollup, data: RollupData) -> bool:
    payload = data.str_payload()
    LOGGER.debug("Echoing '%s'", payload)
    rollup.report(str2hex(payload))
    return True


if __name__ == '__main__':
    app.run()
