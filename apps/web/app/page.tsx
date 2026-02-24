import Link from 'next/link'

export default function HomePage() {
  return <div className="card"><h2>AI 职业替代风险评估 + Agent 定制</h2><p>通过对话式流程完成风险评估、工具推荐与Agent配置。</p><Link href="/evaluate"><button>开始评估</button></Link></div>
}
