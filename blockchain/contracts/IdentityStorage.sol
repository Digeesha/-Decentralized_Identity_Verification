// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IdentityStorage {
    struct Identity {
        string userHash;
        string faceHash;
    }

    mapping(address => Identity) public identities;

    function registerIdentity(address user, string memory faceHash) public {
        identities[user] = Identity("static-user", faceHash);
    }

    function getIdentity(address user) public view returns (string memory, string memory) {
        Identity memory i = identities[user];
        return (i.userHash, i.faceHash);
    }
}