"use client";
import Gameboard from "@/components/Gameboard";
import { envClient } from "@/utils/clientEnv";
import { GameData } from "@/utils/data";
// import Image from "next/image";

import { IChallenge, IPrize } from "@/utils/models";
import { advanceGame, connectPublicClient, connectWalletClient, contractAbi, getChallenge, newGame, timeToDateUTCString } from "@/utils/utils";
import { use, useEffect, useState } from "react";
import { encodeAbiParameters, formatEther, parseAbiParameters, toHex } from "viem";

export default function ChallengePage({ params }: { params: Promise<{ challenge_id: string }> }) {
  const [challenge, setChallenge] = useState<IChallenge>();
  const [selectedWord, setSelectedWord] = useState<string>("");
  const [wordHistory, setWordHistory] = useState<string[]>();
  const [reasonHistory, setReasonHistory] = useState<string[]>();
  const [gameEnded, setGameEnded] = useState<boolean>(false);
  const [gameSubmitted, setGameSubmitted] = useState<boolean>(false);
  const [transacting, setTransacting] = useState<boolean>(false);
  const [gameData, setGameData] = useState<GameData>();
  const [inputLabel, setInputLabel] = useState<string>("New word");


  const useParams = use(params);
  const now = Date.now()/1000;

  useEffect(() => {
    console.log("Loading challenges");
    getChallenge(useParams.challenge_id as `0x${string}`).then((data) => {
      setChallenge(data);
    });

    newGame({"game_id":useParams.challenge_id}).then((data) => {
      setGameData(data);
    });

    // mockData();

  }, [useParams.challenge_id]);

  async function onWordChange(e: React.FormEvent<HTMLInputElement>) {
    setSelectedWord(e.currentTarget.value);
  }

  async function sendWord() {
    if (!selectedWord || transacting || !gameData) return;
    const localWordHistory = wordHistory ? wordHistory.slice() : new Array<string>();
    const localReasonHistory = reasonHistory ? reasonHistory.slice() : new Array<string>();

    setTransacting(true);

    gameData.words = selectedWord.split(',').map((w) => w.replace(/^\s+|\s+$/g, '').toLowerCase());
    const newGameData = await advanceGame(gameData);
    let advanceState = false;
    if (newGameData) {
      const reason = newGameData?.game_board?.last_move_reasoning || "";
      const lastWordIndex = newGameData?.game_board?.last_visited_tile["py/tuple"];;
      const lastWord = lastWordIndex ? newGameData?.game_board?.tiles[lastWordIndex[0]][lastWordIndex[1]].word : "";
      console.log("lastWord",lastWord);
      for (let i = 0; i < gameData.words.length; i++) {
        localWordHistory.splice(0,0,newGameData.words[i]);
        if (i == gameData.words.length - 1 || newGameData.words[i] == lastWord) {
          localReasonHistory.splice(0,0,reason);
          break;
        } else {
          localReasonHistory.splice(0,0,"");
        }
      }

      switch(newGameData?.game_board?.game_status) {
         case "defeat": { }
         case "victory": {
            setGameEnded(true);
            setInputLabel(`${newGameData?.game_board?.game_status}!! please submit`)
            advanceState = true;
            break;
         }
         case "ongoing": {
            setInputLabel("New word")
            advanceState = true;
            break;
        }
        default: {
          break;
        }
      }
    }

    if (advanceState) {
      setGameData(newGameData);
      setWordHistory(localWordHistory);
      setReasonHistory(localReasonHistory);
    } else {
      setInputLabel("Choose another word")
    }
    setSelectedWord("");
    setTransacting(false);
  }

  async function submitResult() {
    if (!useParams.challenge_id || transacting || !gameEnded || !wordHistory?.length) return;

    const walletClient = await connectWalletClient();
    const client = connectPublicClient();

    if (!client || !walletClient) return;

    setTransacting(true);
    const [address] = await walletClient.requestAddresses();
    if (!address) return;
    try {
        const wordBytesList = new Array<`0x${string}`>();
        for (let i = 0; i < wordHistory.length; i++) {
          const word = wordHistory[wordHistory.length - 1 - i];
          wordBytesList.push(toHex(word));
        }

        const encodedPayload = encodeAbiParameters(
          parseAbiParameters('bytes32,bytes[]'),
          [
            useParams.challenge_id as `0x${string}`,
            wordBytesList
          ]
        );

        const { request } = await client.simulateContract({
            account: address,
            address: envClient.APP_ADDR as `0x${string}`,
            abi: contractAbi.abi,
            functionName: 'runExecution',
            args: [encodedPayload ]
        });
        const txHash = await walletClient.writeContract(request);

        await client.waitForTransactionReceipt(
            { hash: txHash }
        )
        setGameSubmitted(true);
    } catch (e) {
        console.log(e);
    }
    setTransacting(false);
  }

  if (!challenge) return (
    <main className="flex items-center justify-center text-2xl">
      Loading Challenge...
    </main>
  );

  return (
    <main className="grid grid-cols-1 h-full w-full">
      <div className="h-16"></div>
      <div className="flex items-start p-5 h-[calc(100vh-8rem)]">
        <div className="w-72 max-h-full bg-slate-50 rounded-xl m-2 grid grid-cols-1 gap-4 overflow-scroll">
          <div className="grid grid-cols-1 gap-2 p-2 bg-slate-100 text-sm"
          >
            {challenge.challengeId ? (
              <div className="flex justify-around w-full">
                <span className="w-1/3 flex justify-start">
                  Challenge Id
                </span>
                <span className="w-3/5 flex justify-end">
                  {challenge.challengeId.substring(0, 6)}...
                  {challenge.challengeId.substring(
                    challenge.challengeId.length - 4,
                    challenge.challengeId.length,
                  )}
                </span>
              </div>
            ) : (
              <></>
            )}
            <div className="flex justify-around w-full">
              <span className="w-1/3 flex justify-start">Start</span>
              <span className="w-3/5 flex justify-end">
                {timeToDateUTCString(challenge.start)}
              </span>
            </div>
            <div className="flex justify-around w-full">
              <span className="w-1/3 flex justify-start">End</span>
              <span className="w-3/5 flex justify-end">
                {timeToDateUTCString(challenge.end)}
              </span>
            </div>
            <div className="flex justify-around w-full">
              <span className="w-1/3 flex justify-start">Total Prize</span>
              <span className="w-3/5 flex justify-end">
                {parseFloat(formatEther(challenge.totalPrize)).toLocaleString("en", { maximumFractionDigits: 4 })} ETH
              </span>
            </div>
          </div>
          { challenge?.start && challenge?.end && (now >= challenge.start && now <= challenge.end) ?
          <>
            {!gameSubmitted ?
            <div className="h-fit grid grid-cols-1 gap-2 p-2 bg-slate-100">
              <div className="w-full max-w-sm min-w-[200px]">
                <div className="relative">
                  <input onChange={onWordChange} type="text" value={selectedWord}
                    disabled={gameEnded || transacting}
                    className="peer w-full bg-transparent placeholder:text-slate-700 text-black text-sm border border-slate-400 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-500 shadow-sm focus:shadow"
                  />
                  <label className={!selectedWord ? "absolute cursor-text bg-slate-100 px-1 left-2.5 top-2.5 text-slate-700 text-sm transition-all transform origin-left peer-focus:-top-2 peer-focus:left-2.5 peer-focus:text-xs peer-focus:text-slate-400 peer-focus:scale-90" : "absolute cursor-text bg-slate-100 px-1 transition-all transform origin-left -top-2 left-2.5 text-xs text-slate-400 scale-90"}>
                    {inputLabel}
                  </label>
                </div>
              </div>

              {!gameEnded ? <button
                className={"px-8 py-2 rounded-md bg-sky-100 border border-sky-300 shadow-md shadow-sky-50/10 " + (selectedWord && !transacting ? " hover:bg-sky-200" : " cursor-not-allowed")} disabled={!selectedWord || transacting}
                onClick={sendWord}
              >Send Word
              </button> :
              <button
                className={"px-8 py-2 rounded-md bg-emerald-100 border border-emerald-300 hover:bg-emerald-200 shadow-md shadow-emerald-50/10" + (!transacting ? " hover:bg-emerald-200" : " cursor-not-allowed")}
                onClick={submitResult} disabled={transacting}
              > Submit Result
              </button>
              }
            </div> : <></>}
            <div className="h-fit grid grid-cols-1 gap-2 p-2 bg-slate-100">
              {wordHistory?.length ? <>
                <span className="text-md font-medium">History</span>
                {
                  wordHistory.map((word: string, index: number) => {
                    return (
                      <div key={`history-${index}`} className="grid grid-cols-1  hover:bg-slate-200">
                        <span className="text-sm">{wordHistory.length-index}) {word}</span>
                        { reasonHistory && reasonHistory[index] ?
                          <p className="pl-2 text-sm">{reasonHistory[index]}</p> : <></>}

                      </div>
                    );
                  })
                }</> : <span className="text-md"></span> }
            </div>
          </>
        : <span className="text-md">Closed</span>
        }
        </div>


        <div className="w-max flex-1 bg-slate-50 rounded-xl m-2 justify-center grid grid-cols-1 gap-2">

          <Gameboard boardData={gameData}></Gameboard>
          { gameData?.game_board ?
          <div className="grid grid-cols-1 gap-2 pt-2 pl-10 pr-10 bg-slate-100 text-sm"
          >

            <div className="grid grid-cols-2 gap-20">
            <div className="flex justify-between w-full">
              <span className="w-2/5 flex justify-start font-semibold">Status</span>
              <span className="w-3/5 flex justify-end">
                {gameData?.game_board?.game_status} { gameData?.game_board?.game_status == "defeat" ? `(reason: ${gameData?.game_board?.defeat_reason})` : "" } {gameEnded ? ` - score: ${gameData?.game_board?.score}` : "" }
              </span>
            </div>
            <div className="flex justify-between w-full">
              <span className="w-2/5 flex justify-start font-semibold">Last Visited</span>
                <span className="w-2/5 flex justify-end">
                  {gameData?.game_board?.last_visited_tile_type}
                </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-20">
            <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Treasures</span>
              <span className="w-1/5 flex justify-end">
                {gameData?.game_board?.treasure_count}
              </span>
            </div>
              <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Total Moves</span>
                <span className="w-1/5 flex justify-end">
                  {gameData?.game_board?.move_count}
                </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-20">
            <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Max Water Supply</span>
              <span className="w-1/5 flex justify-end">
                {gameData?.game_board?.max_water_supply}
              </span>
            </div>
              <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Supply</span>
                <span className="w-1/5 flex justify-end">
                  {gameData?.game_board?.water_supply}
                </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-20">
            <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Curses</span>
              <span className="w-1/5 flex justify-end">
                {gameData?.game_board?.curse_count}
              </span>
            </div>
              <div className="flex justify-between w-full">
              <span className="w-4/5 flex justify-start font-semibold">Amulets</span>
                <span className="w-1/5 flex justify-end">
                  {gameData?.game_board?.amulet_count} (max {gameData?.game_board?.max_amulet_count })
                </span>
            </div>
          </div>

          </div>
          : <></>}
        </div>


        <div className="w-72 bg-slate-50 rounded-xl m-2 grid grid-cols-1 gap-2">
          { challenge && challenge.prizes?.length ? <>
            {
              challenge.prizes.map((prize: IPrize, index: number) => {
                if (!prize.prize) return (<div key={`prizes-${index}`}></div>);

                return (
                  <div
                    key={`prizes-${index}`}
                    className="grid h-fit grid-cols-1 gap-2 p-5 rounded-xl bg-slate-100 border-slate-400 text-sm hover:bg-slate-200"
                  >
                    <div className="flex justify-around w-full">
                      <span className="w-1/3 flex justify-start">Prize Value</span>
                      <span className="w-3/5 flex justify-end">
                        {parseFloat(formatEther(prize.prize)).toLocaleString("en", { maximumFractionDigits: 4 })} ETH
                      </span>
                    </div>
                    <div className="flex justify-around w-full">
                      <span className="w-1/3 flex justify-start">Treasures</span>
                      <span className="w-3/5 flex justify-end">
                        {prize.nTreasures}
                      </span>
                    </div>
                    {prize.timestamp ? (
                      <>
                      <div className="flex justify-around w-full">
                        <span className="w-1/3 flex justify-start">
                          User
                        </span>
                        <span className="w-3/5 flex justify-end">
                          {prize.user.substring(0, 6)}...
                          {prize.user.substring(
                            prize.user.length - 4,
                            prize.user.length,
                          )}
                        </span>
                      </div>
                      <div className="flex justify-around w-full">
                        <span className="w-1/3 flex justify-start">Date</span>
                        <span className="w-3/5 flex justify-end">
                          {timeToDateUTCString(prize.timestamp)}
                        </span>
                      </div>
                      <div className="flex justify-around w-full">
                        <span className="w-1/3 flex justify-start">Score</span>
                        <span className="w-3/5 flex justify-end">
                          {prize.score}
                        </span>
                      </div>
                      <div className="flex justify-around w-full">
                        <span className="w-1/3 flex justify-start">Moves</span>
                        <span className="w-3/5 flex justify-end">
                          {prize.moves} ({prize.movesLeft} moves left)
                        </span>
                      </div>
                      </>
                    ) : (
                      <div className="font-semibold">Not claimed</div>
                    )}
                  </div>
                );
              })
            } </>
           :
            <></>
          }
        </div>
      </div>
      <div className="h-16 absolute botton-0"></div>
    </main>
  );
}
