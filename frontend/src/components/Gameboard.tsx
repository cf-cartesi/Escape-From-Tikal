
import { BoardCoords, GameboardMap, gameboardMapping,  GameboardState, GameData } from '@/utils/data';
import { HexGrid, Layout, Hexagon, Text, GridGenerator, HexUtils } from 'react-hexgrid';


const layoutConfig = {
  "width": 800,
  "height": 600,
  "layout": { "width": 8, "height": 8, "flat": false, "spacing": 1.05 },
  "origin": { "x": 0, "y": 0 },
  "mapProps": [ 3]
};

export default function Gameboard({boardData}:{boardData: GameData | undefined}) {

  const boardState: GameboardState | undefined = boardData?.game_board;
  const boardMap: GameboardMap | undefined = boardData?.game_map.tiles;

  const generator = GridGenerator.getGenerator("hexagon");
  const hexagons = generator(3);
  const layout = layoutConfig.layout;
  const size = { x: layout.width, y: layout.height };
  // console.log("hexagons",hexagons)
  // console.log("boardState",boardState)


  return (
    <div className='grid grid-cols-1 justify-items-center'>
      {/* bg-[url(/mayan-background.jpeg)] */}

      <HexGrid width={layoutConfig.width} height={layoutConfig.height}>
        <Layout size={size} flat={layout.flat} spacing={layout.spacing} origin={layoutConfig.origin}>
          {
            hexagons.map((hex, i) => {
              let hexText = HexUtils.getID(hex);
              let markerText = "";
              let markerClass = "";
              let className = "";
              if (boardState?.tiles) {
                const hexId = HexUtils.getID(hex);
                const coords:BoardCoords = gameboardMapping[hexId];
                if (coords && boardMap && boardMap[coords[0]]) {
                  const row: Record<string,Record<string,string>> = boardMap[coords[0]];
                  if (row[coords[1]]) {
                    hexText = row[coords[1]].type;
                    // console.log("cell",coords,hexText)
                    switch(row[coords[1]].type) {
                      // case 'word': {
                      //   className = "active";
                      //   hexText = row[coords[1]].word;
                      //   markerClass = "word";
                      //   break;
                      // }
                      case 'curse': {
                        className = "curse";
                        markerText = "curse";
                        break;
                      }
                      case 'water': {
                        className = "water";
                        markerText = "water";
                        break;
                      }
                      case 'trap': {
                        className = "trap";
                        markerText = "trap";
                        break;
                      }
                      case 'treasure': {
                        className = "treasure";
                        markerText = "treasure";
                        break;
                      }
                      case 'amulet': {
                        className = "amulet";
                        markerText = "amulet";
                        break;
                      }
                      case 'exit': {
                        className = "exit";
                        markerText = "exit";
                        break;
                      }
                      case 'empty': {}
                      default: {
                        hexText = "";
                        break;
                      }
                    }
                  }
                }

                if (coords && boardState.tiles[coords[0]]) {
                  const row: Record<string,Record<string,string>> = boardState.tiles[coords[0]];
                  if (row[coords[1]] && row[coords[1]].type == 'word') {
                    className = "active";
                    hexText = row[coords[1]].word;
                    markerClass = "word";
                  }
                }
                if (String(boardState.last_visited_tile['py/tuple'][0]) == coords[0] && String(boardState.last_visited_tile['py/tuple'][1]) == coords[1]) {
                  className = `${className} last`;
                }

              }
              return (
              <Hexagon key={layoutConfig.mapProps[0] + i} q={hex.q} r={hex.r} s={hex.s}
                className={className}>
                <Text className={markerClass}>
                  <span className='word'>{hexText}</span>
                  <br />
                    <span className='marker'>{markerText}</span>
                    {hexText}
                </Text>
              </Hexagon>
            )})
          }
        </Layout>
      </HexGrid>
    </div>
  );
};
