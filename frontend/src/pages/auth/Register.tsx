import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MessageSquare, User, Lock, Mail, KeyRound, Eye, EyeOff, Sun, Moon, ArrowLeft } from 'lucide-react'
import { register, generateCaptcha, verifyCaptcha, sendVerificationCode, getRegistrationStatus } from '@/api/auth'
import { useUIStore } from '@/store/uiStore'
import { cn } from '@/utils/cn'
import { safeInput } from '@/utils/xss'
import { validateUsername, validatePassword, validateEmail, validateVerificationCode } from '@/utils/validation'
import { ButtonLoading } from '@/components/common/Loading'

export function Register() {
  const navigate = useNavigate()
  const { addToast } = useUIStore()

  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [, setRegistrationEnabled] = useState(true)
  const [isDark, setIsDark] = useState(false)

  // Form states
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [email, setEmail] = useState('')
  const [captchaCode, setCaptchaCode] = useState('')
  const [verificationCode, setVerificationCode] = useState('')

  // Captcha states
  const [captchaImage, setCaptchaImage] = useState('')
  const [sessionId] = useState(() => `session_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`)
  const [captchaVerified, setCaptchaVerified] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [verifying, setVerifying] = useState(false)

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    const shouldBeDark = savedTheme === 'dark'
    setIsDark(shouldBeDark)
    document.documentElement.classList.toggle('dark', shouldBeDark)
  }, [])

  const toggleTheme = () => {
    const newIsDark = !isDark
    setIsDark(newIsDark)
    document.documentElement.classList.toggle('dark', newIsDark)
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light')
  }

  useEffect(() => {
    getRegistrationStatus().then((result) => {
      setRegistrationEnabled(result.enabled)
      if (!result.enabled) {
        addToast({ type: 'error', message: '注册功能已关闭' })
        navigate('/login')
      }
    }).catch(() => {})
    loadCaptcha()
  }, [])

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  useEffect(() => {
    if (captchaCode.length === 4 && !captchaVerified && !verifying) {
      handleVerifyCaptchaAuto()
    }
  }, [captchaCode])

  const handleVerifyCaptchaAuto = async () => {
    if (captchaCode.length !== 4 || verifying) return
    setVerifying(true)
    try {
      const result = await verifyCaptcha(sessionId, captchaCode)
      if (result.success) {
        setCaptchaVerified(true)
        addToast({ type: 'success', message: '验证码验证成功' })
      } else {
        setCaptchaVerified(false)
        loadCaptcha()
        addToast({ type: 'error', message: '验证码错误' })
      }
    } catch {
      addToast({ type: 'error', message: '验证失败' })
    } finally {
      setVerifying(false)
    }
  }

  const loadCaptcha = async () => {
    try {
      const result = await generateCaptcha(sessionId)
      if (result.success && result.captcha_image) {
        setCaptchaImage(result.captcha_image)
        setCaptchaVerified(false)
        setCaptchaCode('')
      }
    } catch {
      addToast({ type: 'error', message: '加载验证码失败' })
    }
  }

  const handleSendCode = async () => {
    if (!captchaVerified || !email || countdown > 0) return
    try {
      const result = await sendVerificationCode(email, 'register', sessionId)
      if (result.success) {
        setCountdown(60)
        addToast({ type: 'success', message: '验证码已发送' })
      } else {
        addToast({ type: 'error', message: result.message || '发送失败' })
      }
    } catch {
      addToast({ type: 'error', message: '发送验证码失败' })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      // 验证用户名
      const usernameValidation = validateUsername(username)
      if (!usernameValidation.isValid) {
        addToast({ type: 'error', message: usernameValidation.error })
        setLoading(false)
        return
      }

      // 验证密码
      const passwordValidation = validatePassword(password)
      if (!passwordValidation.isValid) {
        addToast({ type: 'error', message: passwordValidation.error })
        setLoading(false)
        return
      }

      // 验证确认密码
      if (password !== confirmPassword) {
        addToast({ type: 'error', message: '两次输入的密码不一致' })
        setLoading(false)
        return
      }

      // 验证邮箱
      const emailValidation = validateEmail(email)
      if (!emailValidation.isValid) {
        addToast({ type: 'error', message: emailValidation.error })
        setLoading(false)
        return
      }

      // 验证邮箱验证码
      const codeValidation = validateVerificationCode(verificationCode)
      if (!codeValidation.isValid) {
        addToast({ type: 'error', message: codeValidation.error })
        setLoading(false)
        return
      }

      // 对用户输入进行安全处理，防止 XSS
      const safeUsername = safeInput(username)
      const safeEmail = safeInput(email)

      const result = await register({
        username: safeUsername,
        password,
        email: safeEmail,
        verification_code: verificationCode,
        session_id: sessionId
      })

      if (result.success) {
        addToast({ type: 'success', message: '注册成功，请登录' })
        navigate('/login')
      } else {
        addToast({ type: 'error', message: result.message || '注册失败' })
      }
    } catch {
      addToast({ type: 'error', message: '注册失败，请检查网络连接' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 z-50 p-2.5 rounded-lg bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors duration-150"
        title={isDark ? '切换到亮色模式' : '切换到暗色模式'}
      >
        {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="hidden lg:flex lg:w-1/2 bg-slate-900 dark:bg-slate-950 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 to-transparent" />
        <div className="relative z-10 flex flex-col justify-center px-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="flex items-center gap-3 mb-8"
          >
            <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">闲鱼管理系统</span>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="text-4xl font-bold text-white mb-4 leading-tight"
          >
            创建账号<br />开启高效运营
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="text-slate-400 text-lg max-w-md"
          >
            加入数千名闲鱼卖家，使用自动化工具提升运营效率
          </motion.p>
        </div>
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-blue-600/10" />
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-blue-600/5" />
      </motion.div>

      <div className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="lg:hidden text-center mb-8"
          >
            <div className="w-12 h-12 rounded-xl bg-blue-500 text-white mx-auto mb-4 flex items-center justify-center">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">闲鱼管理系统</h1>
          </motion.div>

          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-5 sm:p-8">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Link
                  to="/login"
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <h2 className="text-xl vben-card-title text-slate-900 dark:text-white">注册账号</h2>
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">填写以下信息创建您的账号</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3 sm:space-y-4">
              <div className="input-group">
                <label className="input-label">用户名</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="请输入用户名（3-20个字符）"
                    className="input-ios pl-9"
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">邮箱地址</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="请输入邮箱地址"
                    className="input-ios pl-9"
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码（至少6个字符）"
                    className="input-ios pl-9 pr-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">确认密码</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="请再次输入密码"
                    className="input-ios pl-9 pr-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">图形验证码</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={captchaCode}
                    onChange={(e) => setCaptchaCode(e.target.value)}
                    placeholder="输入验证码"
                    maxLength={4}
                    className="input-ios flex-1"
                    disabled={captchaVerified}
                  />
                  <img
                    src={captchaImage}
                    alt="验证码"
                    onClick={loadCaptcha}
                    className="h-[38px] rounded border border-gray-300 cursor-pointer hover:opacity-80 transition-opacity"
                  />
                </div>
                <p className={cn('text-xs', captchaVerified ? 'text-green-600' : verifying ? 'text-blue-500' : 'text-gray-400')}>
                  {captchaVerified ? '✓ 验证成功' : verifying ? '验证中...' : '点击图片更换验证码'}
                </p>
              </div>

              <div className="input-group">
                <label className="input-label">邮箱验证码</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder="6位数字验证码"
                      maxLength={6}
                      className="input-ios pl-9"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleSendCode}
                    disabled={!captchaVerified || !email || countdown > 0}
                    className="btn-ios-secondary whitespace-nowrap"
                  >
                    {countdown > 0 ? `${countdown}s` : '发送'}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full btn-ios-primary">
                {loading ? <ButtonLoading /> : '注 册'}
              </button>
            </form>

            <p className="text-center mt-6 text-slate-500 dark:text-slate-400 text-sm">
              已有账号？{' '}
              <Link to="/login" className="text-blue-600 dark:text-blue-400 font-medium hover:text-blue-700 dark:hover:text-blue-300">
                立即登录
              </Link>
            </p>
          </div>

          <p className="text-center mt-6 text-slate-400 dark:text-slate-500 text-xs">
            © {new Date().getFullYear()} 招赞助商 ·{' '}
            <a
              href="https://www.xxxx.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 dark:hover:text-blue-400 ml-1 transition-colors"
            >
              www.xxxx.com
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

export default Register
