import Link from "next/link";
import { config } from "@/lib/config";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="font-bold text-xl text-slate-900">
                  {config.NEXT_PUBLIC_APP_NAME}
                </span>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center space-x-6">
              <Link 
                href="#features" 
                className="text-slate-600 hover:text-slate-900 transition-colors"
              >
                Features
              </Link>
              <Link 
                href="#supported-chains" 
                className="text-slate-600 hover:text-slate-900 transition-colors"
              >
                Blockchains
              </Link>
              <Link 
                href="#security" 
                className="text-slate-600 hover:text-slate-900 transition-colors"
              >
                Security
              </Link>
            </nav>
            
            <div className="flex items-center space-x-4">
              <Link
                href="/auth/login"
                className="text-slate-600 hover:text-slate-900 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/auth/register"
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium",
                  "bg-blue-600 text-white hover:bg-blue-700",
                  "h-10 px-4 py-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                )}
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-20 sm:py-32">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
                Multi-Chain Cryptocurrency
                <span className="text-blue-600 block">Made Simple</span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-slate-600 max-w-2xl mx-auto">
                {config.NEXT_PUBLIC_APP_DESCRIPTION}. Send, receive, and manage Bitcoin, 
                Ethereum, Cardano, and Polkadot from one secure platform.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link
                  href="/auth/register"
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium",
                    "bg-blue-600 text-white hover:bg-blue-700",
                    "h-12 px-8 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  )}
                >
                  Create Wallet
                </Link>
                <Link
                  href="#features"
                  className="text-sm font-semibold leading-6 text-slate-900 hover:text-blue-600 transition-colors"
                >
                  Learn more <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Supported Blockchains */}
        <section id="supported-chains" className="py-16 bg-muted/50">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                Supported Blockchains
              </h2>
              <p className="mt-4 text-lg text-slate-600">
                Connect to multiple blockchain networks from a single interface
              </p>
            </div>
            
            <div className="mt-12 grid grid-cols-2 gap-8 md:grid-cols-4">
              {[
                { name: 'Bitcoin', symbol: 'BTC', color: 'text-bitcoin', network: config.NEXT_PUBLIC_BITCOIN_NETWORK },
                { name: 'Ethereum', symbol: 'ETH', color: 'text-ethereum', network: config.NEXT_PUBLIC_ETHEREUM_NETWORK },
                { name: 'Cardano', symbol: 'ADA', color: 'text-cardano', network: config.NEXT_PUBLIC_CARDANO_NETWORK },
                { name: 'Polkadot', symbol: 'DOT', color: 'text-polkadot', network: config.NEXT_PUBLIC_POLKADOT_NETWORK },
              ].map((blockchain) => (
                <div key={blockchain.name} className="text-center">
                  <div className="mx-auto h-16 w-16 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center">
                    <span className={cn("text-2xl font-bold", blockchain.color)}>
                      {blockchain.symbol.charAt(0)}
                    </span>
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">
                    {blockchain.name}
                  </h3>
                  <p className="text-sm text-slate-600 capitalize">
                    {blockchain.network} Network
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-16">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                Platform Features
              </h2>
              <p className="mt-4 text-lg text-slate-600">
                Everything you need for secure multi-chain cryptocurrency management
              </p>
            </div>
            
            <div className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  title: 'Multi-Chain Wallets',
                  description: 'Generate and manage wallets for Bitcoin, Ethereum, Cardano, and Polkadot from a single interface.',
                  icon: '🔗',
                },
                {
                  title: 'Secure Transactions',
                  description: 'Send and receive cryptocurrencies with enterprise-grade security and real-time transaction monitoring.',
                  icon: '🔒',
                },
                {
                  title: 'Real-Time Balances',
                  description: 'View up-to-date balances across all supported blockchains with automatic synchronization.',
                  icon: '⚡',
                },
                {
                  title: 'Transaction History',
                  description: 'Complete transaction history with filtering, search, and detailed blockchain information.',
                  icon: '📊',
                },
                {
                  title: 'Fee Estimation',
                  description: 'Smart fee estimation for optimal transaction costs across different network conditions.',
                  icon: '💰',
                },
                {
                  title: 'Mobile & Web',
                  description: 'Access your wallets from anywhere with responsive web and native mobile applications.',
                  icon: '📱',
                },
              ].map((feature) => (
                <div key={feature.title} className="rounded-lg border bg-white p-6 shadow-sm">
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Security */}
        <section id="security" className="py-16 bg-muted/50">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                Enterprise-Grade Security
              </h2>
              <p className="mt-4 text-lg text-slate-600">
                Your assets are protected by industry-leading security measures
              </p>
            </div>
            
            <div className="mt-12 grid gap-8 md:grid-cols-2">
              {[
                {
                  title: 'Private Key Encryption',
                  description: 'All private keys are encrypted using HashiCorp Vault with AES-256 encryption.',
                },
                {
                  title: 'Multi-Factor Authentication',
                  description: 'Secure your account with 2FA, biometric authentication, and device verification.',
                },
                {
                  title: 'Audit Trails',
                  description: 'Complete transaction audit trails with correlation IDs for full traceability.',
                },
                {
                  title: 'Rate Limiting',
                  description: 'Advanced rate limiting and DDoS protection for all API endpoints.',
                },
              ].map((item) => (
                <div key={item.title} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <span className="text-blue-600">✓</span>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">
                      {item.title}
                    </h3>
                    <p className="text-slate-600">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2">
              <div className="h-6 w-6 rounded bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="font-semibold text-slate-900">
                {config.NEXT_PUBLIC_APP_NAME}
              </span>
              <span className="text-slate-600 text-sm">
                v{config.NEXT_PUBLIC_APP_VERSION}
              </span>
            </div>
            
            <div className="mt-4 md:mt-0 flex items-center space-x-6 text-sm text-slate-600">
              <span>© 2024 Sound Pesa. All rights reserved.</span>
              <Link href="/privacy" className="hover:text-slate-900 transition-colors">
                Privacy
              </Link>
              <Link href="/terms" className="hover:text-slate-900 transition-colors">
                Terms
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
