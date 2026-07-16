// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC721} from "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import {IERC2981} from "@openzeppelin/contracts/interfaces/IERC2981.sol";

/// @title Licensing
/// @notice Automates licensing of models registered in ModelRegistry and splits each payment
///         between the creator (royalty via ERC-2981), the platform (fee), and the current owner.
///         A license grants a buyer time-bounded (or perpetual) access, restricted to a set of
///         permitted use types (a bitmask) that encodes machine-checkable ethical-use constraints.
/// @dev Research angle: (3) licensing & royalties. Payments follow checks-effects-interactions.
contract Licensing {
    struct License {
        uint64 issuedAt;
        uint64 expiresAt; // 0 == perpetual
        uint32 allowedUseTypes; // bitmask: bit i set => use type i permitted
        bool active;
    }

    /// @notice The ModelRegistry these licenses are issued against (also the ERC-2981 royalty source).
    IERC721 public immutable registry;
    /// @notice Recipient of the platform fee.
    address public immutable platform;
    /// @notice Platform fee in basis points (e.g. 250 == 2.5%).
    uint96 public immutable platformFeeBps;

    struct Listing {
        uint256 price; // wei; 0 == not listed
        uint32 allowedUseTypes; // use types granted to buyers
        uint64 duration; // license validity in seconds; 0 == perpetual
    }

    mapping(uint256 tokenId => Listing) public listings;
    mapping(uint256 tokenId => mapping(address user => License)) private _licenses;

    event LicenseListed(uint256 indexed tokenId, uint256 price, uint32 allowedUseTypes, uint64 duration);
    event LicensePurchased(
        uint256 indexed tokenId,
        address indexed buyer,
        uint64 expiresAt,
        uint256 pricePaid,
        uint256 royaltyPaid,
        uint256 platformFee
    );

    error NotModelOwner();
    error NotListed();
    error WrongPrice();
    error PaymentFailed();

    constructor(address registry_, address platform_, uint96 platformFeeBps_) {
        registry = IERC721(registry_);
        platform = platform_;
        platformFeeBps = platformFeeBps_;
    }

    /// @notice List (or re-list) a model for licensing. Only the current model owner may list it.
    function listLicense(uint256 tokenId, uint256 price, uint32 allowedUseTypes, uint64 duration) external {
        if (registry.ownerOf(tokenId) != msg.sender) revert NotModelOwner();
        listings[tokenId] = Listing({price: price, allowedUseTypes: allowedUseTypes, duration: duration});
        emit LicenseListed(tokenId, price, allowedUseTypes, duration);
    }

    /// @notice Buy a license for `tokenId`. Splits the exact payment into creator royalty,
    ///         platform fee, and the remainder to the current owner, then records the license.
    function purchaseLicense(uint256 tokenId) external payable {
        Listing memory listing = listings[tokenId];
        if (listing.price == 0) revert NotListed();
        if (msg.value != listing.price) revert WrongPrice();

        (address royaltyReceiver, uint256 royaltyAmount) =
            IERC2981(address(registry)).royaltyInfo(tokenId, listing.price);

        uint256 fee = (listing.price * platformFeeBps) / 10_000;
        // Defensive clamp so the three payouts never exceed what was paid.
        if (royaltyAmount + fee > listing.price) fee = listing.price - royaltyAmount;
        uint256 toOwner = listing.price - royaltyAmount - fee;
        address owner = registry.ownerOf(tokenId);

        // Effects: record the license before any external call (CEI pattern).
        uint64 expiresAt = listing.duration == 0 ? 0 : uint64(block.timestamp) + listing.duration;
        _licenses[tokenId][msg.sender] = License({
            issuedAt: uint64(block.timestamp),
            expiresAt: expiresAt,
            allowedUseTypes: listing.allowedUseTypes,
            active: true
        });

        // Interactions: pay out.
        _pay(royaltyReceiver, royaltyAmount);
        _pay(platform, fee);
        _pay(owner, toOwner);

        emit LicensePurchased(tokenId, msg.sender, expiresAt, listing.price, royaltyAmount, fee);
    }

    /// @notice True if `user` currently holds a non-expired license for `tokenId`.
    function hasValidLicense(uint256 tokenId, address user) public view returns (bool) {
        License memory l = _licenses[tokenId][user];
        if (!l.active) return false;
        if (l.expiresAt != 0 && l.expiresAt < block.timestamp) return false;
        return true;
    }

    /// @notice True if `user` holds a valid license AND `useType` is permitted by it.
    function isUseAllowed(uint256 tokenId, address user, uint8 useType) external view returns (bool) {
        if (!hasValidLicense(tokenId, user)) return false;
        return (_licenses[tokenId][user].allowedUseTypes & (uint32(1) << useType)) != 0;
    }

    /// @notice Read a user's raw license record.
    function getLicense(uint256 tokenId, address user) external view returns (License memory) {
        return _licenses[tokenId][user];
    }

    function _pay(address to, uint256 amount) private {
        if (amount == 0) return;
        (bool ok,) = payable(to).call{value: amount}("");
        if (!ok) revert PaymentFailed();
    }
}
