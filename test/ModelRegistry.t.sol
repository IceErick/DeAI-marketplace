// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {ModelRegistry} from "../contracts/ModelRegistry.sol";

contract ModelRegistryTest is Test {
    ModelRegistry internal registry;
    address internal creator = makeAddr("creator");
    address internal other = makeAddr("other");

    bytes32 internal constant HASH_V1 = keccak256("model-bytes-v1");
    bytes32 internal constant HASH_V2 = keccak256("model-bytes-v2");

    function setUp() public {
        registry = new ModelRegistry();
    }

    function test_RegisterMintsNftAndStoresMetadata() public {
        vm.prank(creator);
        uint256 tokenId = registry.registerModel("QmCID1", HASH_V1, 500);

        assertEq(registry.ownerOf(tokenId), creator);
        ModelRegistry.Model memory m = registry.getModel(tokenId);
        assertEq(m.ipfsCID, "QmCID1");
        assertEq(m.sha256Hash, HASH_V1);
        assertEq(m.version, 1);
        assertEq(m.creator, creator);
    }

    function test_VerifyDetectsTampering() public {
        vm.prank(creator);
        uint256 tokenId = registry.registerModel("QmCID1", HASH_V1, 500);

        assertTrue(registry.verify(tokenId, HASH_V1)); // untouched file
        assertFalse(registry.verify(tokenId, keccak256("tampered"))); // modified file fails
    }

    function test_UpdateBumpsVersion_OnlyOwner() public {
        vm.prank(creator);
        uint256 tokenId = registry.registerModel("QmCID1", HASH_V1, 500);

        vm.prank(other);
        vm.expectRevert(ModelRegistry.NotTokenOwner.selector);
        registry.updateModel(tokenId, "QmCID2", HASH_V2);

        vm.prank(creator);
        registry.updateModel(tokenId, "QmCID2", HASH_V2);
        assertEq(registry.getModel(tokenId).version, 2);
        assertTrue(registry.verify(tokenId, HASH_V2));
    }

    function test_RoyaltyInfoReflectsCreatorShare() public {
        vm.prank(creator);
        uint256 tokenId = registry.registerModel("QmCID1", HASH_V1, 500); // 5%

        (address receiver, uint256 amount) = registry.royaltyInfo(tokenId, 1 ether);
        assertEq(receiver, creator);
        assertEq(amount, 0.05 ether);
    }
}
