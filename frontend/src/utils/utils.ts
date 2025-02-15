import { createWalletClient, createPublicClient, custom, http, Chain, fromHex, isHex, Abi } from "viem";
import { anvil, holesky } from "viem/chains";
import "viem/window";
import { envClient } from "./clientEnv";
import contractAbiFile from "@/contracts/TikalContest.json"
import { IChallenge, IPrize } from "./models";

export const contractAbi = contractAbiFile;

export const ZERO_ADDRESS = `0x${'0'.repeat(2*20)}`;

const chains:Record<number, Chain> = {};
chains[holesky.id] = holesky;
chains[anvil.id] = anvil;

export function getChain(chainId:number):Chain;
export function getChain(chainId:string):Chain;
export function getChain(chainId:number|string) {
    if (typeof chainId === "string") {
        if (!isHex(chainId)) return null;
        chainId = fromHex(chainId, "number");
    }

    const chain = chains[chainId];
    if (!chain) return null;

    return chain;
}

export async function connectWalletClient() {
  // Check for window.ethereum
  // window.ethereum is an object provided by MetaMask or other web3 wallets
  let transport;
  if (window.ethereum) {
    // If window.ethereum exists, create a custom transport using it
    transport = custom(window.ethereum);
  } else {
    // If window.ethereum is not available, throw an error
    const errorMessage =
      "MetaMask or another web3 wallet is not installed. Please install one to proceed.";
    throw new Error(errorMessage);
  }

  // Declare a Wallet Client
  // This creates a wallet client using the Sepolia chain and the custom transport
  const walletClient = createWalletClient({
    chain: getChain(envClient.NETWORK_CHAIN_ID),
    transport: transport,
  });

  // Return the wallet client
  return walletClient;
}

export function connectPublicClient() {
  // Declare a Public Client
  const publicClient = createPublicClient({
    chain: getChain(envClient.NETWORK_CHAIN_ID),
    transport: http()
    //transport: http(envClient.NETWORK_CHAIN_ID == "0xAA36A7" ? "https://ethereum-sepolia-rpc.publicnode.com" : undefined)
  })

  // Return the public client
  return publicClient;
}

const publicClient = connectPublicClient();

export async function getPrizes(challengeId: `0x${string}`): Promise<IPrize[]> {
  const prizes: IPrize[] = [];

  const prizesRes = await publicClient.readContract({
    address: envClient.APP_ADDR as `0x${string}`,
    abi: contractAbi.abi as Abi,
    functionName: "getPrizes",
    args: [challengeId]
  }) as any[];

  for (let i = 0; i < prizesRes.length; i++) {
    prizes.push({
      challengeId: challengeId,
      nTreasures: BigInt(i),
      escaped: prizesRes[i].escaped,
      moves: prizesRes[i].moves,
      movesLeft: prizesRes[i].movesLeft,
      prize: prizesRes[i].prize,
      score: prizesRes[i].score,
      timestamp: prizesRes[i].timestamp,
      user: prizesRes[i].user
    });
  }
  return prizes;
}

export async function getChallenge(challengeId: `0x${string}`): Promise<IChallenge> {

  const challengeRes = await publicClient.readContract({
    address: envClient.APP_ADDR as `0x${string}`,
    abi: contractAbi.abi as Abi,
    functionName: "challenges",
    args: [challengeId]
  }) as any[];

  const challenge: IChallenge = {
    challengeId: challengeId,
    start: challengeRes[0] as bigint,
    end: challengeRes[1] as bigint,
    creator: challengeRes[2] as `0x${string}`,
    totalPrize: challengeRes[3] as bigint,
    nPrizes: challengeRes[4] as bigint,
    finalized: challengeRes[5] as boolean,
  }

  challenge.prizes = await getPrizes(challengeId);
  return challenge;
}
export async function getChallenges(): Promise<IChallenge[]> {
  const challenges: IChallenge[] = [];

  const nChallenges = await publicClient.readContract({
    address: envClient.APP_ADDR as `0x${string}`,
    abi: contractAbi.abi as Abi,
    functionName: "nChallenges",
    args: []
  }) as number;

  for (let i = 0; i < nChallenges; i++) {
    const challengeId = await publicClient.readContract({
      address: envClient.APP_ADDR as `0x${string}`,
      abi: contractAbi.abi as Abi,
      functionName: "challengeHistory",
      args: [i]
    }) as `0x${string}`;

    challenges.push(await getChallenge(challengeId));
  }

  return challenges;
}

export function timeToDateUTCString(time:bigint) {
  const date = new Date(Number(time)*1000);
  return formatDate(date);
}

export function formatDate(date:Date) {
  const options:Intl.DateTimeFormatOptions = {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
      timeZone: "UTC",
      timeZoneName: "short"
  }

  const dateString = date.toLocaleDateString("en-US", options);
  const [month_day, year, time] = dateString.split(",");
  const [month, day] = month_day.split(" ");
  const finalYear = year.substring(1);

  return `${month}/${day}/${finalYear}, ${time}`;
}
