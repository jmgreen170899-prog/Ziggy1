// Unified theme system using Quantum Blue palette
export const pageThemes = {
  dashboard: {
    primary: 'from-primary-tech-blue to-ai-purple',
    secondary: 'from-blue-50 to-purple-50',
    accent: 'bg-primary-tech-blue/20',
    statusColors: {
      success: 'from-success to-emerald-500',
      warning: 'from-warning to-orange-500',
      error: 'from-danger to-rose-500',
      info: 'from-secondary-aqua to-secondary-cyan'
    },
    darkMode: {
      primary: 'from-primary-deep-blue to-ai-purple',
      secondary: 'from-blue-950 to-purple-950'
    }
  },
  trading: {
    primary: 'from-success to-emerald-600',
    secondary: 'from-green-50 to-emerald-50',
    accent: 'bg-success/20',
    statusColors: {
      buy: 'from-success to-emerald-600',
      sell: 'from-danger to-rose-600',
      hold: 'from-warning to-amber-600',
      active: 'from-secondary-aqua to-secondary-cyan'
    },
    darkMode: {
      primary: 'from-green-900 to-emerald-900',
      secondary: 'from-green-950 to-emerald-950'
    }
  },
  portfolio: {
    primary: 'from-ai-purple to-indigo-600',
    secondary: 'from-purple-50 to-indigo-50',
    accent: 'bg-ai-purple/20',
    statusColors: {
      profit: 'from-success to-emerald-600',
      loss: 'from-danger to-rose-600',
      neutral: 'from-gray-600 to-slate-600',
      growth: 'from-primary-tech-blue to-ai-purple'
    },
    darkMode: {
      primary: 'from-purple-900 to-indigo-900',
      secondary: 'from-purple-950 to-indigo-950'
    }
  },
  chat: {
    primary: 'from-secondary-aqua to-primary-tech-blue',
    secondary: 'from-cyan-50 to-blue-50',
    accent: 'bg-secondary-cyan/20',
    statusColors: {
      ai: 'from-ai-purple to-primary-tech-blue',
      user: 'from-gray-600 to-slate-600',
      system: 'from-warning to-amber-600',
      error: 'from-danger to-rose-600'
    },
    darkMode: {
      primary: 'from-cyan-900 to-blue-900',
      secondary: 'from-cyan-950 to-blue-950'
    }
  },
  market: {
    primary: 'from-orange-600 to-danger',
    secondary: 'from-orange-50 to-red-50',
    accent: 'bg-orange-500/20',
    statusColors: {
      bullish: 'from-success to-emerald-600',
      bearish: 'from-danger to-rose-600',
      volatile: 'from-warning to-orange-600',
      stable: 'from-secondary-aqua to-secondary-cyan'
    },
    darkMode: {
      primary: 'from-orange-900 to-red-900',
      secondary: 'from-orange-950 to-red-950'
    }
  },
  news: {
    primary: 'from-teal-600 to-success',
    secondary: 'from-teal-50 to-green-50',
    accent: 'bg-teal-500/20',
    statusColors: {
      positive: 'from-success to-emerald-600',
      negative: 'from-danger to-rose-600',
      neutral: 'from-gray-600 to-slate-600',
      breaking: 'from-orange-600 to-danger'
    },
    darkMode: {
      primary: 'from-teal-900 to-green-900',
      secondary: 'from-teal-950 to-green-950'
    }
  },
  crypto: {
    primary: 'from-amber-600 to-orange-600',
    secondary: 'from-amber-50 to-orange-50',
    accent: 'bg-amber-500/20',
    statusColors: {
      bitcoin: 'from-orange-600 to-amber-600',
      ethereum: 'from-primary-tech-blue to-ai-purple',
      altcoin: 'from-success to-teal-600',
      defi: 'from-ai-purple to-pink-600'
    },
    darkMode: {
      primary: 'from-amber-900 to-orange-900',
      secondary: 'from-amber-950 to-orange-950'
    }
  }
};

// Quantum Blue color tokens for direct use
export const quantumColors = {
  // Primary
  deepBlue: '#103A71',
  techBlue: '#1B5FA7',
  
  // Secondary
  softCyan: '#51C8F5',
  coolAqua: '#2FA2C9',
  
  // AI Accent
  neuralPurple: '#7A4CE0',
  
  // Semantic
  cleanGreen: '#2ECC71',
  marketRed: '#E74C3C',
  goldYellow: '#F4C542',
  
  // Backgrounds
  lightBg: '#F6F7FA',
  darkBg: '#0E121A',
  
  // Text
  primaryText: '#1C1E24',
  secondaryText: '#5C6270',
};

// Unified animation patterns for natural flow
export const animations = {
  pageTransition: 'transition-all duration-500 ease-in-out',
  cardHover: 'hover:scale-105 hover:shadow-xl transition-all duration-300',
  buttonPress: 'hover:scale-105 active:scale-95 transition-all duration-200',
  fadeIn: 'animate-in fade-in duration-500',
  slideIn: 'animate-in slide-in-from-bottom-4 duration-500',
  pulseGlow: 'animate-pulse shadow-lg',
  smoothBounce: 'hover:animate-bounce'
};

// Natural spacing system
export const spacing = {
  pageContainer: 'space-y-8 p-6',
  sectionGap: 'space-y-6',
  cardPadding: 'p-6',
  headerPadding: 'px-6 py-4',
  contentFlow: 'space-y-4'
};

// Consistent border radius system
export const borderRadius = {
  card: 'rounded-xl',
  button: 'rounded-lg',
  input: 'rounded-md',
  badge: 'rounded-full',
  header: 'rounded-t-xl'
};

// Typography flow system
export const typography = {
  pageTitle: 'text-4xl font-bold bg-gradient-to-r bg-clip-text text-transparent',
  sectionTitle: 'text-2xl font-semibold',
  cardTitle: 'text-lg font-medium',
  subtitle: 'text-lg text-opacity-90',
  body: 'text-base',
  caption: 'text-sm text-opacity-75'
};