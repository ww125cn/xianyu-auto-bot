// 表单验证工具函数

/**
 * 验证用户名
 * @param username 用户名
 * @returns 验证结果和错误信息
 */
export function validateUsername(username: string): { isValid: boolean; error?: string } {
  if (!username) {
    return { isValid: false, error: '用户名不能为空' }
  }
  if (username.length < 3 || username.length > 20) {
    return { isValid: false, error: '用户名长度应在3-20个字符之间' }
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { isValid: false, error: '用户名只能包含字母、数字和下划线' }
  }
  return { isValid: true }
}

/**
 * 验证密码
 * @param password 密码
 * @returns 验证结果和错误信息
 */
export function validatePassword(password: string): { isValid: boolean; error?: string } {
  if (!password) {
    return { isValid: false, error: '密码不能为空' }
  }
  if (password.length < 6) {
    return { isValid: false, error: '密码长度至少为6个字符' }
  }
  // 可以添加更多密码强度验证规则
  return { isValid: true }
}

/**
 * 验证邮箱
 * @param email 邮箱地址
 * @returns 验证结果和错误信息
 */
export function validateEmail(email: string): { isValid: boolean; error?: string } {
  if (!email) {
    return { isValid: false, error: '邮箱不能为空' }
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return { isValid: false, error: '请输入有效的邮箱地址' }
  }
  return { isValid: true }
}

/**
 * 验证验证码
 * @param code 验证码
 * @param length 验证码长度
 * @returns 验证结果和错误信息
 */
export function validateVerificationCode(code: string, length: number = 6): { isValid: boolean; error?: string } {
  if (!code) {
    return { isValid: false, error: '验证码不能为空' }
  }
  if (code.length !== length) {
    return { isValid: false, error: `验证码长度应为${length}位` }
  }
  if (!/^\d+$/.test(code)) {
    return { isValid: false, error: '验证码只能包含数字' }
  }
  return { isValid: true }
}

/**
 * 验证图形验证码
 * @param code 图形验证码
 * @param length 验证码长度
 * @returns 验证结果和错误信息
 */
export function validateCaptcha(code: string, length: number = 4): { isValid: boolean; error?: string } {
  if (!code) {
    return { isValid: false, error: '验证码不能为空' }
  }
  if (code.length !== length) {
    return { isValid: false, error: `验证码长度应为${length}位` }
  }
  return { isValid: true }
}

/**
 * 验证手机号
 * @param phone 手机号
 * @returns 验证结果和错误信息
 */
export function validatePhone(phone: string): { isValid: boolean; error?: string } {
  if (!phone) {
    return { isValid: false, error: '手机号不能为空' }
  }
  const phoneRegex = /^1[3-9]\d{9}$/
  if (!phoneRegex.test(phone)) {
    return { isValid: false, error: '请输入有效的手机号' }
  }
  return { isValid: true }
}

/**
 * 验证URL
 * @param url URL地址
 * @returns 验证结果和错误信息
 */
export function validateUrl(url: string): { isValid: boolean; error?: string } {
  if (!url) {
    return { isValid: false, error: 'URL不能为空' }
  }
  try {
    new URL(url)
    return { isValid: true }
  } catch {
    return { isValid: false, error: '请输入有效的URL地址' }
  }
}

/**
 * 验证非空输入
 * @param value 输入值
 * @param fieldName 字段名称
 * @returns 验证结果和错误信息
 */
export function validateRequired(value: string, fieldName: string): { isValid: boolean; error?: string } {
  if (!value || value.trim() === '') {
    return { isValid: false, error: `${fieldName}不能为空` }
  }
  return { isValid: true }
}

/**
 * 验证输入长度
 * @param value 输入值
 * @param min 最小长度
 * @param max 最大长度
 * @param fieldName 字段名称
 * @returns 验证结果和错误信息
 */
export function validateLength(value: string, min: number, max: number, fieldName: string): { isValid: boolean; error?: string } {
  if (!value) {
    return { isValid: false, error: `${fieldName}不能为空` }
  }
  if (value.length < min) {
    return { isValid: false, error: `${fieldName}长度至少为${min}个字符` }
  }
  if (value.length > max) {
    return { isValid: false, error: `${fieldName}长度不能超过${max}个字符` }
  }
  return { isValid: true }
}
