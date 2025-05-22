const IdentityStorage = artifacts.require("IdentityStorage");

module.exports = function (deployer) {
  deployer.deploy(IdentityStorage);
};
