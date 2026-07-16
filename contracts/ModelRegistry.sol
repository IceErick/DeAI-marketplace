// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC2981} from "@openzeppelin/contracts/token/common/ERC2981.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title ModelRegistry
/// @notice The provenance + ownership + integrity ledger for AI models.
///         Each model is a single NFT (ERC-721) so ownership is unambiguous and transferable.
///         Only *metadata* lives on-chain: the IPFS content id (CID) that points to the real
///         model bytes, plus a SHA-256 hash used to prove the downloaded file was not tampered with.
///         Royalty terms (ERC-2981) are attached per token so resales can pay the original creator.
/// @dev Research angles: (1) integrity & security, (4) usage/provenance trail. See docs/research-methodology.md.
contract ModelRegistry is ERC721, ERC2981, AccessControl {
    /// @notice Platform administrators (e.g. to pause/curate in a later milestone).
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    /// @notice One immutable-ish record per model token. `version` and `updatedAt` change on update;
    ///         the full history is reconstructable from the `ModelRegistered`/`ModelUpdated` events.
    struct Model {
        string ipfsCID; // content address of the model file in IPFS
        bytes32 sha256Hash; // integrity hash of the model file
        uint256 version; // starts at 1, incremented on each update
        uint64 createdAt; // block timestamp of registration
        uint64 updatedAt; // block timestamp of the latest update
        address creator; // original registrant (royalty beneficiary)
    }

    uint256 private _nextId = 1;
    mapping(uint256 tokenId => Model) private _models;

    event ModelRegistered(
        uint256 indexed tokenId, address indexed creator, string ipfsCID, bytes32 sha256Hash, uint96 royaltyBps
    );
    event ModelUpdated(uint256 indexed tokenId, uint256 newVersion, string ipfsCID, bytes32 sha256Hash);

    error NotTokenOwner();
    error UnknownModel();

    constructor() ERC721("DeAI Model", "DEAI") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /// @notice Register a new model. Mints an ownership NFT to the caller and records its metadata.
    /// @param ipfsCID     IPFS content id of the uploaded model file.
    /// @param sha256Hash  SHA-256 of the model file (integrity anchor).
    /// @param royaltyBps  Creator royalty in basis points (e.g. 500 = 5%), enforced on resale via ERC-2981.
    /// @return tokenId    The id of the newly minted model NFT.
    function registerModel(string calldata ipfsCID, bytes32 sha256Hash, uint96 royaltyBps)
        external
        returns (uint256 tokenId)
    {
        tokenId = _nextId++;
        _safeMint(msg.sender, tokenId);
        _setTokenRoyalty(tokenId, msg.sender, royaltyBps);

        _models[tokenId] = Model({
            ipfsCID: ipfsCID,
            sha256Hash: sha256Hash,
            version: 1,
            createdAt: uint64(block.timestamp),
            updatedAt: uint64(block.timestamp),
            creator: msg.sender
        });

        emit ModelRegistered(tokenId, msg.sender, ipfsCID, sha256Hash, royaltyBps);
    }

    /// @notice Publish a new version of an existing model. Only the current owner may update it.
    /// @dev The previous versions remain provable through the emitted event history.
    function updateModel(uint256 tokenId, string calldata ipfsCID, bytes32 sha256Hash) external {
        if (ownerOf(tokenId) != msg.sender) revert NotTokenOwner();

        Model storage m = _models[tokenId];
        m.ipfsCID = ipfsCID;
        m.sha256Hash = sha256Hash;
        m.version += 1;
        m.updatedAt = uint64(block.timestamp);

        emit ModelUpdated(tokenId, m.version, ipfsCID, sha256Hash);
    }

    /// @notice Read the full metadata record for a model.
    function getModel(uint256 tokenId) external view returns (Model memory) {
        if (_ownerOf(tokenId) == address(0)) revert UnknownModel();
        return _models[tokenId];
    }

    /// @notice Integrity check: does `candidateHash` match the on-chain hash for this model?
    /// @dev A client re-hashes the file it downloaded from IPFS and calls this. A tampered file fails.
    function verify(uint256 tokenId, bytes32 candidateHash) external view returns (bool) {
        if (_ownerOf(tokenId) == address(0)) revert UnknownModel();
        return _models[tokenId].sha256Hash == candidateHash;
    }

    // ERC721 + ERC2981 + AccessControl each declare supportsInterface; Solidity requires one override.
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC2981, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
