export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold">Sound Pesa</h1>
        <p className="text-xl">Multi-chain Cryptocurrency Platform</p>
      </div>

      <div className="relative flex place-items-center">
        <h2 className="text-2xl font-semibold">
          Welcome to Sound Pesa Development Environment
        </h2>
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-4 lg:text-left">
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h3 className="mb-3 text-2xl font-semibold">
            Bitcoin
          </h3>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Secure Bitcoin transactions and wallet management
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h3 className="mb-3 text-2xl font-semibold">
            Ethereum
          </h3>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            ETH and ERC-20 token support with smart contracts
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h3 className="mb-3 text-2xl font-semibold">
            Cardano
          </h3>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            ADA transactions and native token support
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h3 className="mb-3 text-2xl font-semibold">
            Polkadot
          </h3>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            DOT transfers and cross-chain functionality
          </p>
        </div>
      </div>
    </main>
  )
}