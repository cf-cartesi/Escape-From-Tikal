import jsonpickle
from flask import Flask, request, jsonify
import core_engine.tikal_core as tkl_core
import traceback
import json

app = Flask(__name__)

@app.route('/new_game', methods=['POST'])
def create_new_game():
    try:
        data = request.get_json()

        if data:
            if "game_id" in data.keys():
                hex_game_id = data["game_id"]
                int_game_id = int(hex_game_id, 16)

                print(f"Creating new game state with game_id {int_game_id}")

                #Generating a new game state
                new_game_state = tkl_core.GameState(game_id=int_game_id, new_game=True)                
            
                #Removing some indexes to make the response simpler
                del new_game_state.game_board.words_on_board
                del new_game_state.game_board.word_tile_coords_set
        
                serialized_output_state = jsonpickle.encode(new_game_state)

                response = {
                    "status": "success",
                    "message": f"Game was created successfully for game_id {int_game_id}",
                    "game_state": json.loads(serialized_output_state)
                }

                return jsonify(response), 200
            else:
                response = {
                    "status": "error",
                    "message": "No game_id provided", 
                }
                return jsonify(response), 400   

        response = {
            "status": "error",
            "message": "Must provide a game_id to create a new game"
        }
        return jsonify(response), 400

    except Exception as e:
        error_message = f"{e}\nTraceback\n\n{traceback.format_exc()}"
        print(error_message)
        response = {
            "status": "error",
            "message": f"Error creating a new game",
            "error": error_message 
        }
        return jsonify(response), 500 

@app.route('/advance_game', methods=['POST'])
def advance_game():
    try:
        data = request.get_data(as_text=True)
                
        if data:
            #Deserialize game state
            print("Start of data\n" + "-"*80)
            print(data)
            print("End of data\n" + "-"*80)
            deserialized_state = jsonpickle.decode(data)
            current_game_state = tkl_core.GameState(game_map=deserialized_state.game_map,
                                                    game_board=deserialized_state.game_board,
                                                    words=deserialized_state.words,
                                                    game_id=deserialized_state.game_id,
                                                    new_game=False)

            #Create game executor and load map and board
            game_executor = tkl_core.GameExecutor(current_game_state.game_board, current_game_state.game_map)

            #Execute game
            gameboard_output = game_executor.execute_game(current_game_state.words)
        
            #Remove indexes
            del gameboard_output.words_on_board
            del gameboard_output.word_tile_coords_set
            
            current_game_state.game_board = gameboard_output

            serialized_output_state = jsonpickle.encode(current_game_state)

            response = {
                "status": "success",
                "message": f"Successfully advanced state for game_id {current_game_state.game_id}",
                "game_state": json.loads(serialized_output_state)
            }

            return jsonify(response), 200            

        response = {
            "status": "error",
            "message": "Must provide a game state json to advance the game state"
        }
        return jsonify(response), 400

    except Exception as e:
        error_message = f"{e}\nTraceback\n\n{traceback.format_exc()}"
        print(error_message)
        response = {
            "status": "error",
            "message": f"Error advancing game state",
            "error": error_message 
        }
        return jsonify(response), 500 
if __name__ == '__main__':
    app.run(debug=True)  # Set debug=False in production