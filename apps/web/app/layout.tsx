import './globals.css'
import Link from 'next/link'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <main>
          <h1>JobShield AI</h1>
          <nav style={{display:'flex',gap:12}}>
            <Link href="/">Home</Link><Link href="/evaluate">Evaluate</Link><Link href="/dashboard">Dashboard</Link><Link href="/agent">Agent</Link>
          </nav>
          {children}
        </main>
      </body>
    </html>
  )
}
