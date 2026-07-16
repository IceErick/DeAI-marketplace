// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {ModelRegistry} from "../contracts/ModelRegistry.sol";
import {Licensing} from "../contracts/Licensing.sol";
import {UsageLog} from "../contracts/UsageLog.sol";

/// @notice Deploys the three contracts and wires them together.
///         The deployer becomes the platform fee recipient. Fee defaults to 2.5% (250 bps).
///         Run: `make deploy` (see Makefile) or
///         `forge script script/Deploy.s.sol:Deploy --rpc-url <url> --private-key <pk> --broadcast`.
contract Deploy is Script {
    function run() external returns (ModelRegistry registry, Licensing licensing, UsageLog usageLog) {
        uint96 platformFeeBps = 250; // 2.5%

        vm.startBroadcast();

        registry = new ModelRegistry();
        licensing = new Licensing(address(registry), msg.sender, platformFeeBps);
        usageLog = new UsageLog(address(licensing));

        vm.stopBroadcast();

        console.log("ModelRegistry:", address(registry));
        console.log("Licensing:    ", address(licensing));
        console.log("UsageLog:     ", address(usageLog));
        console.log("Platform fee (bps):", platformFeeBps);
    }
}
