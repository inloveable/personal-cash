/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#050A07',
        panel: '#0A120C',
        raise: '#101C12',
        line: '#1C2E20',
        neon: '#22C55E',
        'neon-bright': '#4ADE80',
        'neon-dim': '#166534',
        danger: '#EF4444',
        gain: '#F87171',
        'gain-dim': '#991B1B',
        amber: '#F59E0B',
        ink: '#E7F5EC',
        sub: '#8FAF9B',
        mute: '#52705F',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"PingFang SC"', '"Noto Sans SC"', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 12px rgba(34, 197, 94, 0.25)',
        'glow-lg': '0 0 28px rgba(34, 197, 94, 0.35)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
