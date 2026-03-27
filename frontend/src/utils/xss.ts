// XSS 防护工具函数

/**
 * 转义 HTML 特殊字符，防止 XSS 攻击
 * @param str 输入字符串
 * @returns 转义后的字符串
 */
export function escapeHtml(str: string): string {
  if (!str) return ''
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * 清理用户输入，移除潜在的恶意脚本
 * @param input 用户输入
 * @returns 清理后的输入
 */
export function sanitizeInput(input: string): string {
  if (!input) return ''
  
  // 移除 script 标签
  let sanitized = input.replace(/<script[^>]*>.*?<\/script>/gi, '')
  
  // 移除 onclick、onload 等事件属性
  sanitized = sanitized.replace(/on\w+\s*=\s*["'].*?["']/gi, '')
  
  // 移除 JavaScript 伪协议
  sanitized = sanitized.replace(/javascript:[^"']*/gi, '')
  
  return sanitized
}

/**
 * 安全地设置元素的 HTML 内容
 * @param element DOM 元素
 * @param content 要设置的内容
 */
export function setSafeHtml(element: Element, content: string): void {
  if (!element) return
  element.textContent = content
}

/**
 * 验证输入是否包含潜在的 XSS 攻击代码
 * @param input 用户输入
 * @returns 是否包含潜在的 XSS 攻击代码
 */
export function containsXss(input: string): boolean {
  if (!input) return false
  
  // 检测 script 标签
  const scriptRegex = /<script[^>]*>.*?<\/script>/gi
  if (scriptRegex.test(input)) return true
  
  // 检测事件属性
  const eventRegex = /on\w+\s*=\s*["'].*?["']/gi
  if (eventRegex.test(input)) return true
  
  // 检测 JavaScript 伪协议
  const jsProtocolRegex = /javascript:[^"']*/gi
  if (jsProtocolRegex.test(input)) return true
  
  return false
}

/**
 * 安全地处理用户输入，用于显示在页面上
 * @param input 用户输入
 * @returns 安全处理后的输入
 */
export function safeInput(input: string): string {
  return escapeHtml(sanitizeInput(input))
}
