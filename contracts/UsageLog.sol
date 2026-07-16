// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface ILicensing {
    function hasValidLicense(uint256 tokenId, address user) external view returns (bool);
    function isUseAllowed(uint256 tokenId, address user, uint8 useType) external view returns (bool);
}

/// @title UsageLog
/// @notice Immutable, append-only audit trail of how licensed models are used. Every call is gated
///         by the Licensing contract, so only valid licensees using a permitted use type can log.
///         The full history is reconstructable from `UsageLogged` events (nothing is stored beyond a
///         counter) which keeps per-call gas low.
/// @dev Research angle: (4) usage tracking & ethics. Use types are an application-defined enum, e.g.
///      0=inference, 1=fine-tuning, 2=redistribution — see docs/research-methodology.md.
contract UsageLog {
    ILicensing public immutable licensing;

    /// @notice Total number of usage events ever logged (cheap on-chain aggregate for dashboards).
    uint256 public totalLogs;

    event UsageLogged(uint256 indexed tokenId, address indexed user, uint8 useType, uint64 timestamp);

    error NoValidLicense();
    error UseTypeNotAllowed();

    constructor(address licensing_) {
        licensing = ILicensing(licensing_);
    }

    /// @notice Record one usage event for `tokenId` by the caller. Reverts unless the caller holds a
    ///         valid license that permits `useType`.
    function logUsage(uint256 tokenId, uint8 useType) external {
        if (!licensing.hasValidLicense(tokenId, msg.sender)) revert NoValidLicense();
        if (!licensing.isUseAllowed(tokenId, msg.sender, useType)) revert UseTypeNotAllowed();

        unchecked {
            totalLogs += 1;
        }
        emit UsageLogged(tokenId, msg.sender, useType, uint64(block.timestamp));
    }
}
