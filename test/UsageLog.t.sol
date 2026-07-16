// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {ModelRegistry} from "../contracts/ModelRegistry.sol";
import {Licensing} from "../contracts/Licensing.sol";
import {UsageLog} from "../contracts/UsageLog.sol";

contract UsageLogTest is Test {
    ModelRegistry internal registry;
    Licensing internal licensing;
    UsageLog internal usageLog;

    address internal creator = makeAddr("creator");
    address internal buyer = makeAddr("buyer");
    address internal platform = makeAddr("platform");

    uint256 internal constant PRICE = 1 ether;
    uint32 internal constant USE_INFERENCE = uint32(1) << 0;
    uint256 internal tokenId;

    function setUp() public {
        registry = new ModelRegistry();
        licensing = new Licensing(address(registry), platform, 250);
        usageLog = new UsageLog(address(licensing));

        vm.prank(creator);
        tokenId = registry.registerModel("QmCID1", keccak256("v1"), 500);
        vm.prank(creator);
        licensing.listLicense(tokenId, PRICE, USE_INFERENCE, 0); // perpetual, inference only

        vm.deal(buyer, 10 ether);
    }

    function test_UnlicensedUserCannotLog() public {
        vm.prank(buyer);
        vm.expectRevert(UsageLog.NoValidLicense.selector);
        usageLog.logUsage(tokenId, 0);
    }

    function test_LicensedUserLogsAllowedUse() public {
        vm.prank(buyer);
        licensing.purchaseLicense{value: PRICE}(tokenId);

        vm.prank(buyer);
        vm.expectEmit(true, true, false, true);
        emit UsageLog.UsageLogged(tokenId, buyer, 0, uint64(block.timestamp));
        usageLog.logUsage(tokenId, 0);

        assertEq(usageLog.totalLogs(), 1);
    }

    function test_DisallowedUseTypeReverts() public {
        vm.prank(buyer);
        licensing.purchaseLicense{value: PRICE}(tokenId);

        vm.prank(buyer);
        vm.expectRevert(UsageLog.UseTypeNotAllowed.selector);
        usageLog.logUsage(tokenId, 1); // fine-tuning not permitted by this license
    }
}
