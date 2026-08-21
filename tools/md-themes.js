/**
 * md-themes.js — Starline 公众号主题色板库
 * ============================================
 * 移植自 starline-gzh-design 技能 theme-index.md 的 9 套主题
 * 设计变量。每个主题 = 一组色板参数，供 md-components.js 使用。
 *
 * 字段说明：
 *   id          — 主题标识
 *   name        — 中文名
 *   description — 适用场景描述
 *   primary     — 主色
 *   secondary   — 辅色（渐变用）
 *   softBg      — 浅底色（引言/提示块）
 *   softBorder  — 浅边框色
 *   deep        — 深字色（引言大字）
 *   ink         — 标题/正文深色
 *   underline   — 正文关键词下划线色
 *   hlBg        — 高亮底色
 *   codeBg      — 行内代码底
 *   codeText    — 行内代码字
 */

const MdThemes = {
  themes: [
    {
      id: 'moyu-green', name: '摸鱼绿',
      description: '教程、测评、清单、工具盘点（卡片丰富、信息密度高，默认推荐）',
      primary: '#059669', secondary: '#10B981',
      softBg: '#F0FDF4', softBorder: 'rgba(5,150,105,0.15)',
      deep: '#065F46', ink: '#111827',
      underline: '#A7F3D0', hlBg: '#FDE68A',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
    {
      id: 'tech-cobalt', name: '科技钴蓝',
      description: 'AI 工具、开发教程、产品说明、工作流指南（冷静清晰、黄蓝对比）',
      primary: '#1D4ED8', secondary: '#2563EB',
      softBg: '#EFF6FF', softBorder: 'rgba(29,78,216,0.15)',
      deep: '#1E3A8A', ink: '#111827',
      underline: '#93C5FD', hlBg: '#FDE68A',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
    {
      id: 'red-white', name: '红白色系',
      description: '深度分析、观点、力量感话题（经典编辑风，红色克制点睛）',
      primary: '#DC2626', secondary: '#EF4444',
      softBg: '#FEF2F2', softBorder: 'rgba(220,38,38,0.15)',
      deep: '#991B1B', ink: '#111827',
      underline: '#FECACA', hlBg: '#FDE68A',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
    {
      id: 'graphite-minimal', name: '石墨极简',
      description: '设计、科技评论、专业观点、高端品牌（极简克制、全灰阶）',
      primary: '#52525B', secondary: '#71717A',
      softBg: '#F4F4F5', softBorder: 'rgba(82,82,91,0.15)',
      deep: '#3F3F46', ink: '#1C1917',
      underline: '#52525B', hlBg: '#E4E4E7',
      codeBg: '#F4F4F5', codeText: '#27272A',
    },
    {
      id: 'apple-open-course', name: '苹果公开课',
      description: '方法论、公开课、知识框架、商业策略与教程（读者任务优先、细线大留白）',
      primary: '#0066CC', secondary: '#2563EB',
      softBg: '#F5F5F7', softBorder: 'rgba(0,102,204,0.12)',
      deep: '#003E7E', ink: '#1D1D1F',
      underline: '#0066CC', hlBg: '#E8F1FB',
      codeBg: '#F5F5F7', codeText: '#1D1D1F',
    },
    {
      id: 'zen-whitespace', name: '留白禅意',
      description: '禅意冥想、极简生活、深度随笔、艺术留白（呼吸感最强）',
      primary: '#4A5D52', secondary: '#6B806F',
      softBg: '#F1F5F2', softBorder: 'rgba(74,93,82,0.15)',
      deep: '#263B2C', ink: '#2A2A2A',
      underline: '#B5C8BC', hlBg: '#EDF1ED',
      codeBg: '#F1F5F2', codeText: '#3A4A3E',
    },
    {
      id: 'moyu-ticket', name: '摸鱼票据',
      description: '测评、工具对比、创意评测（票据/门票视觉隐喻，星级评分+编号+硬阴影卡片）',
      primary: '#059669', secondary: '#10B981',
      softBg: '#ECFDF5', softBorder: 'rgba(5,150,105,0.15)',
      deep: '#163C34', ink: '#111827',
      underline: '#A7F3D0', hlBg: '#FDE68A',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
    {
      id: 'olive-journal', name: '橄榄手记',
      description: '内刊手记、深度评测、案例复盘、系统性说明文档（编辑部内刊质感）',
      primary: '#ED7B2F', secondary: '#F59E0B',
      softBg: '#FFF7ED', softBorder: 'rgba(237,123,47,0.18)',
      deep: '#9A3412', ink: '#1E1F23',
      underline: '#ED7B2F', hlBg: '#FDE68A',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
    {
      id: 'klein-blue', name: '克莱因蓝艺术展册',
      description: '艺术评论、品牌叙事、深度观点、人物特稿（高纯度蓝色锚点、展册式结构）',
      primary: '#002FA7', secondary: '#2563EB',
      softBg: '#EFF6FF', softBorder: 'rgba(0,47,167,0.15)',
      deep: '#001C63', ink: '#111111',
      underline: '#002FA7', hlBg: '#E8EEFF',
      codeBg: '#F3F4F6', codeText: '#1F2937',
    },
  ],

  get(id) {
    return this.themes.find(t => t.id === id) || this.themes[0];
  },

  all() {
    return this.themes;
  },
};
