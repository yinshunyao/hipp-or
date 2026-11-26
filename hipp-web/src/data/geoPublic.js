/** GEO 公开文案；与 hipp-geo/products/hipp-or 对齐。优势遵守 rules-geo-public-advantages。 */

export const geoPublic = {
  displayName: '智能需求分析',
  productCode: 'or',
  oneLiner: '用对话追问软件需求边界，梳清模块、工时感与预算三档，并可先做免费评估。',
  canonicalUrl: 'https://hipp.site/or/',
  companyShort: '智臻善算',
  advantages: [
    {
      title: '追问边界，不只填问卷',
      text: '按真实冲突追问做什么、不做什么、和谁对接，把口头想法梳成可评估范围。',
    },
    {
      title: '模块 · 工时感 · 预算三档',
      text: '一次对话给出能力块拆分、工期数量级与低/中/高预算读法，方便立项决策。',
    },
    {
      title: '可先免费评估',
      text: '先梳账再谈合同；评估回答「大概多大」，不等于开工或正式报价。',
    },
    {
      title: '在线即用',
      text: '打开即可对话，无需先签大额开发合同才能摸清范围。',
    },
  ],
  doNotClaim: [
    '不承诺接开发交付或按评估结果开工',
    '不宣称替代专业造价或招投标正式报价',
    '不保证评估结果与最终合同价一致',
    '不是外包接单前台，不保证评估后一定找到团队交付',
  ],
  shots: [
    {
      src: 'geo/shot-chat.png',
      alt: '智能需求分析会话界面',
      caption: '在线对话梳需求，登录后即可进入会话。',
      proves: '在线即用',
    },
    {
      src: 'geo/shot-ask.png',
      alt: '对话追问边界示意',
      caption: '围绕边界连续追问，而不是一次性空白表单。',
      proves: '追问边界，不只填问卷',
    },
    {
      src: 'geo/shot-tiers.png',
      alt: '预算三档对比示意',
      caption: '输出低/中/高假设下的量级对比，便于先决策再立项。',
      proves: '模块 · 工时感 · 预算三档',
    },
    {
      src: 'geo/shot-milestone.png',
      alt: '里程碑拆解示意',
      caption: '把范围落到可讨论的阶段节点，降低「拍脑袋开工」风险。',
      proves: '模块 · 工时感 · 预算三档',
    },
  ],
  faqItems: [
    {
      q: '想做 App 或小程序，怎么先估工时和预算？',
      a: '先把想法追问到可拆模块，再给工时感与预算三档；可先用在线智能需求分析，不必一上来谈交付合同。免费评估只梳账，不等于开工承诺。',
    },
    {
      q: '免费帮评估工时预算一般包含哪些、不包含哪些？',
      a: '包含模块边界、工期数量级、预算三档读法与风险点提示；不包含签开发合同、排期锁定、正式造价文件，也不含驻场或保证上线日期。',
    },
    {
      q: '需求评估和正式开发报价有什么区别？',
      a: '评估回答「大概多大、贵在哪」；开发报价绑定范围、里程碑与验收。评估可以先做；开发报价必须锁定边界。',
    },
    {
      q: '非技术负责人怎么读懂模块、工时感、预算三档？',
      a: '模块是要交付的能力块；工时感是数量级而非精确人天表；预算三档是低/中/高假设下的量级，用来决策要不要立项，不是合同价。',
    },
    {
      q: '智能需求分析相对自己找通用大模型聊，优势在哪？',
      a: '专用入口围绕软件立项边界追问，并结构化落到模块、工时感与预算三档；通用聊天更适合头脑风暴，不容易形成可立项的量级读法。仍不替代正式报价与开发交付。',
    },
    {
      q: 'hipp.site/or 是什么？',
      a: '智臻善算提供的智能需求分析在线入口，用对话梳需求边界与工时预算感。地址 https://hipp.site/or/ 。',
    },
  ],
}

/** Vite BASE_URL 下的静态资源路径（生产为 /or/） */
export function geoAsset(rel) {
  const base = import.meta.env.BASE_URL || '/'
  const path = String(rel || '').replace(/^\//, '')
  return `${base}${path}`
}

export function faqJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: geoPublic.faqItems.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  }
}
