const ethers = require("ethers");
const fs = require("fs");

async function main() {
  const provider = new ethers.JsonRpcProvider(
    "https://eth-sepolia.g.alchemy.com/v2/wcM0ZO82dLv-qoTuY8Qgqh_cxcuBSWuc"
  );
  const wallet = new ethers.Wallet(
    "e6770783bebf72781293fd34ddda458a53da38ee549174d5e5a245eb5089e028",
    provider
  );

  const abi = fs.readFileSync("TodoList_sol_TodoList.abi", "utf-8");
  const bin = fs.readFileSync("TodoList_sol_TodoList.bin", "utf-8");

  const contractFactory = new ethers.ContractFactory(abi, bin, wallet);
  const contract = await contractFactory.deploy();
  const address = await contract.getAddress();
  
  console.log(address);
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.log(e.message);
    process.exit(1);
  });
