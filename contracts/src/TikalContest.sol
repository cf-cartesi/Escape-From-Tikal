// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./EvmCoprocessorAdapter.sol";

contract TikalContest is EvmCoprocessorAdapter {
    error ChallengeFinalized();
    error InvalidParam(string reason);
    error InvalidPrize(string reason);

    constructor(
        address _taskIssuerAddress,
        bytes32 _machineHash
    ) CoprocessorAdapter(_taskIssuerAddress, _machineHash) {}

    function runExecution(bytes calldata payload) external {
        this.evmInput(msg.sender, payload);
    }

    event ReceivedNotice(
        bytes32 indexed challendge_id,
        address indexed user,
        uint256 timestamp,
        bytes32 payloadHash
    );

    event ChallengeNotice(
        bytes32 indexed challendge_id,
        address indexed user,
        uint256 indexed treasures,
        uint256 timestamp,
        uint256 score,
        uint256 moves,
        uint256 movesLeft,
        bool victory,
        bytes32 payloadHash
    );

    struct Result {
        uint256 prize;
        uint256 timestamp;
        uint256 score;
        uint256 moves;
        uint256 movesLeft;
        address user;
        bool victory;
    }
    struct Challenge {
        uint256 start;
        uint256 end;
        address creator;
        uint256 totalPrize;
        uint256 nPrizes;
        mapping(uint8 => Result) prizes;
        bool finalized;
    }

    mapping(bytes32 => Challenge) public challenges;
    mapping(uint256 => bytes32) public challengeHistory;
    uint256 public nChallenges;

    function getPrizes(
        bytes32 challengeId
    ) public view returns (Result[] memory) {
        Result[] memory prizes = new Result[](challenges[challengeId].nPrizes);

        for (uint8 i = 0; i < challenges[challengeId].nPrizes; ++i) {
            prizes[i].prize = challenges[challengeId].prizes[i].prize;
            prizes[i].timestamp = challenges[challengeId].prizes[i].timestamp;
            prizes[i].score = challenges[challengeId].prizes[i].score;
            prizes[i].moves = challenges[challengeId].prizes[i].moves;
            prizes[i].movesLeft = challenges[challengeId].prizes[i].movesLeft;
            prizes[i].user = challenges[challengeId].prizes[i].user;
            prizes[i].victory = challenges[challengeId].prizes[i].victory;
        }
        return prizes;
    }

    function createChallenge(
        bytes32 challengeId,
        address creator,
        uint256 end,
        uint256[] calldata prizes
    ) external payable {
        if (challenges[challengeId].end != 0) revert InvalidParam("duplicate");
        if (end <= block.timestamp) revert InvalidParam("end");
        if (prizes.length > 256) revert InvalidParam("prize length");

        uint256 totalPrize;
        for (uint8 i = 0; i < prizes.length; ++i) {
            totalPrize += prizes[i];
            challenges[challengeId].prizes[i].prize = prizes[i];
        }
        if (totalPrize != msg.value) revert InvalidParam("total prize");

        challenges[challengeId].start = block.timestamp;
        challenges[challengeId].end = end;
        challenges[challengeId].creator = creator;
        challenges[challengeId].totalPrize = totalPrize;
        challenges[challengeId].nPrizes = prizes.length;
        challengeHistory[nChallenges] = challengeId;
        nChallenges++;
    }

    function finalizeChallenge(bytes32 challengeId) external {
        if (challenges[challengeId].finalized)
            revert ChallengeFinalized();
        if (challenges[challengeId].end == 0)
            revert InvalidParam("not created");
        if (challenges[challengeId].end >= block.timestamp)
            revert InvalidParam("not ended");

        challenges[challengeId].finalized = true;

        bool sent;
        uint256 remainingPrize = challenges[challengeId].totalPrize;
        for (uint8 i = 0; i < challenges[challengeId].nPrizes; ++i) {
            if (challenges[challengeId].prizes[i].user != address(0)) {
                if (challenges[challengeId].prizes[i].prize > remainingPrize)
                    revert InvalidPrize("insufficient amount");
                remainingPrize -= challenges[challengeId].prizes[i].prize;

                (sent, ) = challenges[challengeId].prizes[i].user.call{
                    value: challenges[challengeId].prizes[i].prize
                }("");
                if (!sent) revert InvalidPrize("error tx");
            }
        }
        (sent, ) = challenges[challengeId].creator.call{value: remainingPrize}(
            ""
        );
        if (!sent) revert InvalidPrize("error tx");
    }

    // Notice class from backend
    // class ChallengeNotice(BaseModel):
    //     challenge_id: abi.Bytes32
    //     timestamp: abi.UInt256
    //     score: abi.UInt256
    //     n_moves: abi.UInt256
    //     n_moves_left: abi.UInt256
    //     user: abi.Address
    //     n_treasures: abi.UInt8
    //     victory: abi.Bool

    function handleNotice(
        bytes32 payloadHash,
        bytes memory notice
    ) internal override {
        (
            bytes32 chId,
            uint256 ts,
            uint256 score,
            uint256 moves,
            uint256 movesLeft,
            address user,
            uint8 trasures,
            bool victory
        ) = abi.decode(
                notice,
                (
                    bytes32,
                    uint256,
                    uint256,
                    uint256,
                    uint256,
                    address,
                    uint8,
                    bool
                )
            );
        emit ReceivedNotice(chId, user, ts, payloadHash);
        if (ts >= challenges[chId].start && ts <= challenges[chId].end) {
            uint8 prizeIndex = victory ? trasures : 0;
            if (score > 0 && score > challenges[chId].prizes[prizeIndex].score) {
                challenges[chId].prizes[prizeIndex].timestamp = ts;
                challenges[chId].prizes[prizeIndex].score = score;
                challenges[chId].prizes[prizeIndex].moves = moves;
                challenges[chId].prizes[prizeIndex].movesLeft = movesLeft;
                challenges[chId].prizes[prizeIndex].user = user;
                challenges[chId].prizes[prizeIndex].victory = victory;
            }
            emit ChallengeNotice(
                chId,
                user,
                trasures,
                ts,
                score,
                moves,
                movesLeft,
                victory,
                payloadHash
            );
        }
    }
}
