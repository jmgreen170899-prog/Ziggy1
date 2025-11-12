// Unified theme system for natural flow across all pages
export const pageThemes = {
  dashboard: {
    primary: 'from-blue-600 to-purple-600',
    secondary: 'from-blue-50 to-purple-50',
    accent: 'bg-blue-500/20',
    statusColors: {
      success: 'from-green-500 to-emerald-500',
      warning: 'from-yellow-500 to-orange-500',
      error: 'from-red-500 to-rose-500',
      info: 'from-blue-500 to-cyan-500'
    },
    darkMode: {
      primary: 'from-blue-900 to-purple-900',
      secondary: 'from-blue-950 to-purple-950'
    }
  },
  trading: {
    primary: 'from-green-600 to-emerald-600',
    secondary: 'from-green-50 to-emerald-50',
    accent: 'bg-green-500/20',
    statusColors: {
      buy: 'from-green-600 to-emerald-600',
      sell: 'from-red-600 to-rose-600',
      hold: 'from-yellow-600 to-amber-600',
      active: 'from-blue-600 to-cyan-600'
    },
    darkMode: {
      primary: 'from-green-900 to-emerald-900',
      secondary: 'from-green-950 to-emerald-950'
    }
  },
  portfolio: {
    primary: 'from-purple-600 to-indigo-600',
    secondary: 'from-purple-50 to-indigo-50',
    accent: 'bg-purple-500/20',
    statusColors: {
      profit: 'from-green-600 to-emerald-600',
      loss: 'from-red-600 to-rose-600',
      neutral: 'from-gray-600 to-slate-600',
      growth: 'from-blue-600 to-purple-600'
    },
    darkMode: {
      primary: 'from-purple-900 to-indigo-900',
      secondary: 'from-purple-950 to-indigo-950'
    }
  },
  chat: {
    primary: 'from-cyan-600 to-blue-600',
    secondary: 'from-cyan-50 to-blue-50',
    accent: 'bg-cyan-500/20',
    statusColors: {
      ai: 'from-cyan-600 to-blue-600',
      user: 'from-gray-600 to-slate-600',
      system: 'from-yellow-600 to-amber-600',
      error: 'from-red-600 to-rose-600'
    },
    darkMode: {
      primary: 'from-cyan-900 to-blue-900',
      secondary: 'from-cyan-950 to-blue-950'
    }
  },
  market: {
    primary: 'from-orange-600 to-red-600',
    secondary: 'from-orange-50 to-red-50',
    accent: 'bg-orange-500/20',
    statusColors: {
      bullish: 'from-green-600 to-emerald-600',
      bearish: 'from-red-600 to-rose-600',
      volatile: 'from-yellow-600 to-orange-600',
      stable: 'from-blue-600 to-cyan-600'
    },
    darkMode: {
      primary: 'from-orange-900 to-red-900',
      secondary: 'from-orange-950 to-red-950'
    }
  },
  news: {
    primary: 'from-teal-600 to-green-600',
    secondary: 'from-teal-50 to-green-50',
    accent: 'bg-teal-500/20',
    statusColors: {
      positive: 'from-green-600 to-emerald-600',
      negative: 'from-red-600 to-rose-600',
      neutral: 'from-gray-600 to-slate-600',
      breaking: 'from-orange-600 to-red-600'
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
      ethereum: 'from-blue-600 to-purple-600',
      altcoin: 'from-green-600 to-teal-600',
      defi: 'from-purple-600 to-pink-600'
    },
    darkMode: {
      primary: 'from-amber-900 to-orange-900',
      secondary: 'from-amber-950 to-orange-950'
    }
  }
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