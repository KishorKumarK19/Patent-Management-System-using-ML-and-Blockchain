// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

error NotOwner();
error NotValidPatent();

contract RoyaltyToken {
    string public title;
    address public owner;
    uint256 public monthlyPayInWei;
    bool public isValidPatent=true;

    struct RoyaltyUser {
        uint256 validityDate;
        uint256 months;
    }

    mapping(address => RoyaltyUser) public royaltyUsers;

    constructor(string memory _title, address _owner) {
        title = _title;
        owner = _owner;
        monthlyPayInWei = 10000000000000000;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    modifier onlyValidPatent() {
        require(isValidPatent, "Not a valid patent");
        _;
    }

    function calculateFutureTimestamp(
        uint256 initialTimestamp,
        uint256 monthsAhead
    ) internal pure returns (uint256) {
        return initialTimestamp + (2628000 * monthsAhead); // 30.44 days per month
    }

    function royaltyPayment(uint256 _months) public payable onlyValidPatent {
        uint256 requiredPayment = monthlyPayInWei * _months;
        require(msg.value >= requiredPayment, "Insufficient ETH sent");

        royaltyUsers[msg.sender] = RoyaltyUser(
            calculateFutureTimestamp(block.timestamp, _months),
            _months
        );

        (bool callSuccess, ) = payable(owner).call{value: requiredPayment}("");
        require(callSuccess, "Failed to send payment to owner");

        (bool callSuccess1, ) = payable(msg.sender).call{value: msg.value - requiredPayment}("");
        require(callSuccess1, "Failed to send payment to owner");
    }

    function toggleToValidPatent() public onlyOwner {
        isValidPatent = true;
    }
}