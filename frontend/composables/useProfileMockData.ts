// Deterministic mock data for widgets (seeded per username/id)

const STEAM_GAMES = [
  { name: 'Counter-Strike 2', hours: 1247 },
  { name: 'Dota 2', hours: 856 },
  { name: 'Rust', hours: 312 },
  { name: 'Cyberpunk 2077', hours: 189 },
  { name: 'Elden Ring', hours: 67 },
  { name: 'GTA V', hours: 412 },
  { name: 'Hollow Knight', hours: 45 },
  { name: 'Terraria', hours: 234 },
]

const TRACKS = [
  { artist: 'Billie Eilish', track: 'bad guy' },
  { artist: 'The Weeknd', track: 'Blinding Lights' },
  { artist: 'Daft Punk', track: 'Get Lucky' },
  { artist: 'Gorillaz', track: 'Feel Good Inc.' },
  { artist: 'Arctic Monkeys', track: 'R U Mine?' },
  { artist: 'Radiohead', track: 'Creep' },
  { artist: 'Tame Impala', track: 'The Less I Know The Better' },
  { artist: 'MGMT', track: 'Electric Feel' },
]

const REPO_NAMES = [
  'awesome-list', 'dotfiles', 'personal-site', 'api-server',
  'discord-bot', 'cli-tool', 'portfolio', 'utils',
]

function strSeed(str: string): number {
  let n = 5381
  for (let i = 0; i < str.length; i++) {
    n = ((n << 5) + n) ^ str.charCodeAt(i)
    n = n & 0x7fffffff
  }
  return n || 1
}

function seededRand(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

export function useProfileMockData() {
  function steamGames(steamId: string) {
    if (!steamId) return []
    const rand = seededRand(strSeed(steamId))
    return [...STEAM_GAMES].sort(() => rand() - 0.5).slice(0, 3)
  }

  function lastfmTrack(username: string) {
    const s = strSeed(username)
    return TRACKS[s % TRACKS.length]
  }

  function ghHeatmap(username: string): number[] {
    const rand = seededRand(strSeed(username))
    return Array.from({ length: 364 }, () => {
      const r = rand()
      if (r > 0.92) return 4
      if (r > 0.82) return 3
      if (r > 0.70) return 2
      if (r > 0.55) return 1
      return 0
    })
  }

  function ghStats(username: string) {
    const rand = seededRand(strSeed(username + '_s'))
    return {
      repos: Math.floor(rand() * 80 + 5),
      contributions: Math.floor(rand() * 1800 + 200),
    }
  }

  function ghRepos(username: string): string[] {
    const rand = seededRand(strSeed(username + '_r'))
    return [...REPO_NAMES].sort(() => rand() - 0.5).slice(0, 3)
  }

  function eloToLevel(elo: number): number {
    if (elo < 801) return 1
    if (elo < 951) return 2
    if (elo < 1101) return 3
    if (elo < 1251) return 4
    if (elo < 1401) return 5
    if (elo < 1551) return 6
    if (elo < 1751) return 7
    if (elo < 2001) return 8
    if (elo < 2251) return 9
    return 10
  }

  function faceitData(nickname: string) {
    if (!nickname) return { elo: 0, level: 1, kd: '0.00', winRate: 0, matches: 0 }
    const rand = seededRand(strSeed(nickname))
    const elo = Math.floor(rand() * 2800 + 300)
    return {
      elo,
      level: eloToLevel(elo),
      kd: (rand() * 0.8 + 0.7).toFixed(2),
      winRate: Math.floor(rand() * 20 + 45),
      matches: Math.floor(rand() * 1500 + 100),
    }
  }

  function faceitLevelColor(level: number): string {
    if (level <= 3) return '#636380'
    if (level <= 6) return '#f5a623'
    if (level <= 8) return '#e05c28'
    return '#cc1c2c'
  }

  return { steamGames, lastfmTrack, ghHeatmap, ghStats, ghRepos, faceitData, faceitLevelColor }
}
