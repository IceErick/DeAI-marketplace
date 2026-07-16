// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {ModelRegistry} from "../contracts/ModelRegistry.sol";
import {Licensing} from "../contracts/Licensing.sol";

contract LicensingTest is Test {
    ModelRegistry internal registry;
    Licensing internal licensing;

    address internal creator = makeAddr("creator");
    address internal buyer = makeAddr("buyer");
    address internal platform = makeAddr("platform");

    uint96 internal constant FEE_BPS = 250; // 2.5%
    uint256 internal constant PRICE = 1 ether;
    uint32 internal constant USE_INFERENCE = uint32(1) << 0; // bit 0
    uint256 internal tokenId;

    function setUp() public {
        registry = new ModelRegistry();
        licensing = new Licensing(address(registry), platform, FEE_BPS);

        vm.prank(creator);
        tokenId = registry.registerModel("QmCID1", keccak256("v1"), 500); // 5% royalty

        vm.prank(creator);
        licensing.listLicense(tokenId, PRICE, USE_INFERENCE, 30 days);

        vm.deal(buyer, 10 ether);
    }

    function test_PurchaseSplitsPaymentAndGrantsLicense() public {
        uint256 creatorBefore = creator.balance;
        uint256 platformBefore = platform.balance;

        vm.prank(buyer);
        licensing.purchaseLicense{value: PRICE}(tokenId);

        // creator is both royalty receiver (5%) and current owner (remainder) => gets price - fee.
        uint256 fee = (PRICE * FEE_BPS) / 10_000; // 2.5%
        assertEq(platform.balance - platformBefore, fee);
        assertEq(creator.balance - creatorBefore, PRICE - fee);

        assertTrue(licensing.hasValidLicense(tokenId, buyer));
        assertTrue(licensing.isUseAllowed(tokenId, buyer, 0)); // inference allowed
        assertFalse(licensing.isUseAllowed(tokenId, buyer, 1)); // fine-tuning not allowed
    }

    function test_WrongPriceReverts() public {
        vm.prank(buyer);
        vm.expectRevert(Licensing.WrongPrice.selector);
        licensing.purchaseLicense{value: 0.5 ether}(tokenId);
    }

    function test_LicenseExpires() public {
        vm.prank(buyer);
        licensing.purchaseLicense{value: PRICE}(tokenId);
        assertTrue(licensing.hasValidLicense(tokenId, buyer));

        vm.warp(block.timestamp + 31 days);
        assertFalse(licensing.hasValidLicense(tokenId, buyer));
    }

    function test_OnlyOwnerCanList() public {
        vm.prank(buyer);
        vm.expectRevert(Licensing.NotModelOwner.selector);
        licensing.listLicense(tokenId, PRICE, USE_INFERENCE, 0);
    }
}
